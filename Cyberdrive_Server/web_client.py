#!/usr/bin/env python3
"""
CyberDrive - Client USB (PC Local)
Se connecte à l'ESP32 via USB et communique avec le serveur Proxmox
Remplace la partie "serial communication" du main.py original
"""

import serial
import serial.tools.list_ports
import socketio
import time
import json
import threading
import logging
import sys
from datetime import datetime
from pathlib import Path

# ==================== Configuration ====================

# À MODIFIER: URL de ton serveur Proxmox
SERVER_URL = 'http://192.168.1.100:5000'  # ← CHANGE MOI !

SERIAL_BAUDRATE = 115200
RECONNECT_DELAY = 5  # secondes

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== Client SocketIO ====================

sio = socketio.Client(
    reconnection=True,
    reconnection_delay=RECONNECT_DELAY,
    reconnection_attempts=0,  # Infini
    logger=False
)

# ==================== Variables Globales ====================

serial_connection = None
running = True
current_vehicle_id = None

# ==================== Fonctions Série ====================

def list_serial_ports():
    """Liste tous les ports série disponibles"""
    ports = serial.tools.list_ports.comports()
    logger.info("Ports série disponibles:")
    for i, port in enumerate(ports):
        logger.info(f"  [{i}] {port.device} - {port.description}")
    return [port.device for port in ports]

def detect_esp32_port():
    """Auto-détection de l'ESP32"""
    ports = serial.tools.list_ports.comports()
    
    # Identifiants ESP32 courants
    esp32_ids = [
        "CP210", "CP2102",  # SiLabs CP210x
        "CH340", "CH9102",  # WCH CH340/CH9102
        "FTDI",             # FTDI
        "USB-SERIAL",
        "Silicon Labs"
    ]
    
    for port in ports:
        desc = port.description.upper()
        for identifier in esp32_ids:
            if identifier.upper() in desc:
                logger.info(f"✓ ESP32 détecté: {port.device} ({port.description})")
                return port.device
    
    logger.warning("ESP32 non détecté automatiquement")
    return None

def connect_serial(port=None):
    """Connexion au port série (ESP32)"""
    global serial_connection
    
    if port is None:
        # Auto-détection
        port = detect_esp32_port()
        if not port:
            ports = list_serial_ports()
            if ports:
                port = ports[0]
                logger.warning(f"Utilisation du premier port: {port}")
            else:
                logger.error("Aucun port série trouvé!")
                return False
    
    try:
        serial_connection = serial.Serial(
            port,
            SERIAL_BAUDRATE,
            timeout=1,
            write_timeout=1
        )
        
        # Flush buffers
        serial_connection.reset_input_buffer()
        serial_connection.reset_output_buffer()
        
        logger.info(f"✓ Connecté à {port} @ {SERIAL_BAUDRATE} baud")
        time.sleep(2)  # Attendre l'initialisation ESP32
        return True
        
    except Exception as e:
        logger.error(f"✗ Erreur connexion série: {e}")
        return False

def disconnect_serial():
    """Déconnexion du port série"""
    global serial_connection
    
    if serial_connection and serial_connection.is_open:
        serial_connection.close()
        logger.info("Port série fermé")

# ==================== Thread Lecture Série ====================

def read_serial_thread():
    """Thread de lecture continue des données série"""
    global running, serial_connection
    
    logger.info("Thread de lecture série démarré")
    
    while running:
        try:
            if serial_connection and serial_connection.is_open:
                if serial_connection.in_waiting > 0:
                    raw_line = serial_connection.readline()
                    
                    try:
                        line = raw_line.decode('utf-8', errors='ignore').strip()
                        
                        if line:
                            logger.debug(f"ESP32 → {line}")
                            
                            # Parser la télémétrie
                            if line.startswith("TELEM:"):
                                parse_and_send_telemetry(line)
                            
                            elif line.startswith("ACK:") or line.startswith("HEARTBEAT:"):
                                logger.debug(f"ESP32: {line}")
                            
                            else:
                                # Autre message
                                logger.info(f"ESP32: {line}")
                    
                    except Exception as e:
                        logger.warning(f"Erreur décodage: {e}")
        
        except Exception as e:
            logger.error(f"Erreur lecture série: {e}")
            time.sleep(1)
        
        time.sleep(0.01)  # 100 Hz max

def parse_and_send_telemetry(telem_string):
    """
    Parse la télémétrie ESP32 et l'envoie au serveur
    Format: TELEM:{dir}:{thr}:{dist}:{batt}:{rx}
    """
    try:
        parts = telem_string.strip().split(':')
        
        if len(parts) >= 6 and parts[0] == 'TELEM':
            telemetry = {
                'direction': int(parts[1]),
                'throttle': int(parts[2]),
                'distance_cm': int(parts[3]),
                'battery_voltage': float(parts[4]),
                'rx_active': bool(int(parts[5])),
                'timestamp': datetime.now().isoformat()
            }
            
            # Envoyer au serveur via WebSocket
            if sio.connected:
                sio.emit('vehicle_telemetry', telemetry)
            
    except Exception as e:
        logger.warning(f"Erreur parsing télémétrie: {e}")

def write_to_serial(data):
    """Écrire des données sur le port série"""
    global serial_connection
    
    try:
        if serial_connection and serial_connection.is_open:
            if isinstance(data, dict):
                # Convertir la commande en format ESP32
                # Format: CMD:MOVE:{dir}:{thr}\n
                direction = data.get('direction', 1500)
                throttle = data.get('throttle', 1500)
                cmd_str = f"CMD:MOVE:{direction}:{throttle}\n"
            else:
                cmd_str = str(data) + "\n"
            
            serial_connection.write(cmd_str.encode('utf-8'))
            logger.debug(f"Serveur → ESP32: {cmd_str.strip()}")
            return True
    
    except Exception as e:
        logger.error(f"Erreur écriture série: {e}")
        return False

# ==================== WebSocket Events ====================

@sio.event
def connect():
    """Connecté au serveur"""
    logger.info("✓ Connecté au serveur Proxmox")
    
    # S'enregistrer en tant que client USB
    sio.emit('usb_client_register', {
        'port': serial_connection.port if serial_connection else 'unknown',
        'baudrate': SERIAL_BAUDRATE,
        'timestamp': datetime.now().isoformat()
    })

@sio.event
def disconnect():
    """Déconnecté du serveur"""
    logger.warning("✗ Déconnecté du serveur")

@sio.event
def connect_error(data):
    """Erreur de connexion"""
    logger.error(f"Erreur connexion serveur: {data}")

@sio.on('usb_registration_ok')
def on_registration_ok(data):
    """Le serveur a confirmé l'enregistrement"""
    logger.info("✓ Enregistrement USB confirmé")
    
    # Notifier que le véhicule est connecté (si série OK)
    if serial_connection and serial_connection.is_open:
        sio.emit('vehicle_connected', {
            'vehicle_id': current_vehicle_id or 'rc_car_001',
            'timestamp': datetime.now().isoformat()
        })

@sio.on('vehicle_command')
def on_vehicle_command(data):
    """Commande reçue du serveur pour le véhicule"""
    logger.info(f"Commande reçue: DIR={data.get('direction')} THR={data.get('throttle')}")
    
    # Envoyer sur le port série
    write_to_serial(data)

@sio.on('connect_vehicle')
def on_connect_vehicle(data):
    """Le serveur demande de se connecter à un véhicule spécifique"""
    global current_vehicle_id
    
    vehicle_id = data.get('vehicle_id')
    logger.info(f"Demande de connexion au véhicule: {vehicle_id}")
    
    current_vehicle_id = vehicle_id
    
    # Notifier la connexion
    if serial_connection and serial_connection.is_open:
        sio.emit('vehicle_connected', {
            'vehicle_id': vehicle_id,
            'timestamp': datetime.now().isoformat()
        })

# ==================== Main ====================

def print_banner():
    """Bannière de démarrage"""
    print("\n" + "=" * 70)
    print("  🚗 CyberDrive - Client USB")
    print("=" * 70)
    print(f"  Serveur:  {SERVER_URL}")
    print(f"  Baudrate: {SERIAL_BAUDRATE}")
    print("=" * 70 + "\n")

def main():
    """Point d'entrée principal"""
    global running, current_vehicle_id
    
    print_banner()
    
    # 1. Connexion série à l'ESP32
    logger.info("Recherche de l'ESP32...")
    ports = list_serial_ports()
    
    if not ports:
        logger.error("ERREUR: Aucun port série trouvé!")
        logger.error("Vérifie que l'ESP32 est branché en USB.")
        return
    
    print("\nChoisir le port série de l'ESP32:")
    for i, port in enumerate(ports):
        print(f"  [{i}] {port}")
    
    try:
        choice = input(f"\nPort [0-{len(ports)-1}] (Entrée pour auto-detect): ").strip()
        
        if choice == "":
            selected_port = detect_esp32_port() or ports[0]
        else:
            selected_port = ports[int(choice)]
    
    except (ValueError, IndexError):
        selected_port = ports[0]
    
    if not connect_serial(selected_port):
        logger.error("Impossible de se connecter au port série!")
        return
    
    # 2. Connexion au serveur Proxmox
    logger.info(f"\nConnexion au serveur: {SERVER_URL}")
    
    try:
        sio.connect(SERVER_URL)
    except Exception as e:
        logger.error(f"Impossible de se connecter au serveur: {e}")
        logger.info("Vérif: Le serveur tourne ? L'URL est correcte ?")
        logger.info("Le client va continuer d'essayer de se reconnecter...")
    
    # 3. Démarrer le thread de lecture série
    read_thread = threading.Thread(target=read_serial_thread, daemon=True)
    read_thread.start()
    
    print("\n" + "=" * 70)
    print("✓ Client USB démarré")
    print(f"  Port série: {selected_port}")
    print(f"  Serveur:    {SERVER_URL}")
    print("\n  Appuie sur Ctrl+C pour quitter")
    print("=" * 70 + "\n")
    
    # 4. Boucle principale (keepalive)
    try:
        while running:
            time.sleep(1)
            
            # Ping périodique si connecté
            if sio.connected:
                sio.emit('ping')
    
    except KeyboardInterrupt:
        print("\n\n✓ Arrêt demandé...")
        running = False
        
        # Cleanup
        if sio.connected:
            sio.emit('vehicle_disconnected')
            time.sleep(0.5)
            sio.disconnect()
        
        disconnect_serial()
        
        print("✓ Client arrêté proprement.")

if __name__ == '__main__':
    # Configuration personnalisée via argument
    if len(sys.argv) > 1:
        SERVER_URL = sys.argv[1]
        logger.info(f"URL serveur personnalisée: {SERVER_URL}")
    
    main()
