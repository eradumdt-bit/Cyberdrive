#!/usr/bin/env python3
"""
CyberDrive - Main Server (Web Version)
Serveur backend pour Proxmox - Version web de main.py
Gère la logique métier sans UI locale, avec interface web accessible de partout
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit, disconnect
from flask_cors import CORS
from datetime import datetime
import json
import logging
import os
import sys
import threading
import time
from pathlib import Path

# Add project root to path (si besoin de tes modules existants)
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# ==================== Configuration ====================

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'cyberdrive-secret-change-me')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload

CORS(app, resources={r"/*": {"origins": "*"}})

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    ping_timeout=60,
    ping_interval=25,
    max_http_buffer_size=10 * 1024 * 1024
)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== État Global ====================

class ServerState:
    """État global du serveur"""
    def __init__(self):
        self.web_clients = 0  # Clients web connectés
        self.usb_client_connected = False  # Client USB (PC local) connecté
        self.usb_client_sid = None  # Socket ID du client USB
        self.vehicle_connected = False  # Véhicule ESP32/Arduino connecté
        self.current_vehicle_id = None
        
        # Dernières données télémétrie
        self.last_telemetry = {
            'direction': 1500,
            'throttle': 1500,
            'distance_cm': -1,
            'battery_voltage': 0.0,
            'rx_active': False,
            'obstacle_detected': False,
            'mode': 'unknown',
            'timestamp': None
        }
        
        # Dernière frame caméra
        self.last_camera_frame = None
        
        # Statistiques
        self.commands_sent = 0
        self.telemetry_received = 0
        self.start_time = datetime.now()

state = ServerState()

# ==================== Utilitaires ====================

def load_vehicle_configs():
    """Charge toutes les configurations de véhicules"""
    vehicles = []
    vehicles_dir = Path('config/vehicles')
    
    if vehicles_dir.exists():
        for json_file in vehicles_dir.glob('*.json'):
            try:
                with open(json_file, 'r') as f:
                    vehicle = json.load(f)
                    vehicles.append(vehicle)
                    logger.info(f"Loaded vehicle: {vehicle.get('name', 'Unknown')}")
            except Exception as e:
                logger.error(f"Failed to load {json_file}: {e}")
    
    return vehicles

# ==================== Routes HTTP ====================

@app.route('/')
def index():
    """Page d'accueil - Dashboard principal"""
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """Retourne le status complet du serveur"""
    uptime = (datetime.now() - state.start_time).total_seconds()
    
    return jsonify({
        'status': 'online',
        'uptime_seconds': uptime,
        'web_clients': state.web_clients,
        'usb_client_connected': state.usb_client_connected,
        'vehicle_connected': state.vehicle_connected,
        'current_vehicle': state.current_vehicle_id,
        'commands_sent': state.commands_sent,
        'telemetry_received': state.telemetry_received,
        'last_telemetry': state.last_telemetry
    })

@app.route('/api/vehicles')
def api_vehicles():
    """Liste tous les véhicules configurés"""
    vehicles = load_vehicle_configs()
    return jsonify(vehicles)

@app.route('/api/telemetry')
def api_telemetry():
    """Retourne la dernière télémétrie"""
    return jsonify(state.last_telemetry)

# ==================== WebSocket Events ====================

@socketio.on('connect')
def handle_connect():
    """Nouveau client connecté"""
    logger.info(f"Client connecté: {request.sid}")
    emit('server_status', {
        'status': 'connected',
        'timestamp': datetime.now().isoformat(),
        'usb_client_online': state.usb_client_connected,
        'vehicle_online': state.vehicle_connected
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Client déconnecté"""
    global state
    
    # Vérifier si c'est le client USB qui se déconnecte
    if request.sid == state.usb_client_sid:
        logger.warning("Client USB déconnecté!")
        state.usb_client_connected = False
        state.usb_client_sid = None
        state.vehicle_connected = False
        
        # Notifier tous les clients web
        socketio.emit('usb_client_disconnected', {'timestamp': datetime.now().isoformat()})
    else:
        # Client web normal
        state.web_clients = max(0, state.web_clients - 1)
    
    logger.info(f"Client déconnecté: {request.sid} (Web clients: {state.web_clients})")

# ==================== Événements Client USB ====================

@socketio.on('usb_client_register')
def handle_usb_client_register(data):
    """
    Le client USB s'enregistre auprès du serveur
    C'est le PC local avec l'ESP32 branché en USB
    """
    global state
    
    state.usb_client_connected = True
    state.usb_client_sid = request.sid
    
    logger.info(f"✓ Client USB enregistré: {request.sid}")
    logger.info(f"  Port série: {data.get('port', 'unknown')}")
    
    # Confirmer au client USB
    emit('usb_registration_ok', {
        'server_time': datetime.now().isoformat(),
        'message': 'USB client registered successfully'
    })
    
    # Notifier tous les clients web
    socketio.emit('usb_client_connected', {
        'timestamp': datetime.now().isoformat(),
        'port': data.get('port', 'unknown')
    }, broadcast=True)

@socketio.on('vehicle_connected')
def handle_vehicle_connected(data):
    """Le véhicule ESP32/Arduino est connecté"""
    global state
    
    state.vehicle_connected = True
    state.current_vehicle_id = data.get('vehicle_id', 'unknown')
    
    logger.info(f"✓ Véhicule connecté: {state.current_vehicle_id}")
    
    # Notifier tous les clients
    socketio.emit('vehicle_status', {
        'connected': True,
        'vehicle_id': state.current_vehicle_id,
        'timestamp': datetime.now().isoformat()
    }, broadcast=True)

@socketio.on('vehicle_disconnected')
def handle_vehicle_disconnected():
    """Le véhicule est déconnecté"""
    global state
    
    logger.warning("✗ Véhicule déconnecté")
    state.vehicle_connected = False
    
    socketio.emit('vehicle_status', {
        'connected': False,
        'timestamp': datetime.now().isoformat()
    }, broadcast=True)

@socketio.on('vehicle_telemetry')
def handle_vehicle_telemetry(data):
    """
    Réception de télémétrie depuis le client USB
    Le client USB lit le port série et envoie les données ici
    """
    global state
    
    try:
        # Mettre à jour l'état
        state.last_telemetry.update(data)
        state.last_telemetry['timestamp'] = datetime.now().isoformat()
        state.telemetry_received += 1
        
        # Broadcast à tous les clients web
        socketio.emit('telemetry_update', state.last_telemetry, broadcast=True)
        
    except Exception as e:
        logger.error(f"Erreur traitement télémétrie: {e}")

@socketio.on('camera_frame')
def handle_camera_frame(data):
    """Réception d'une frame caméra (base64)"""
    global state
    
    try:
        state.last_camera_frame = data.get('frame')
        
        # Broadcast aux clients web (sauf l'émetteur)
        socketio.emit('camera_update', {
            'frame': state.last_camera_frame,
            'timestamp': datetime.now().isoformat()
        }, broadcast=True, include_self=False)
        
    except Exception as e:
        logger.error(f"Erreur traitement caméra: {e}")

# ==================== Événements Clients Web ====================

@socketio.on('web_client_hello')
def handle_web_client_hello():
    """Un client web s'identifie"""
    global state
    state.web_clients += 1
    logger.info(f"Client web connecté (Total: {state.web_clients})")

@socketio.on('send_command')
def handle_send_command(data):
    """
    Un client web veut envoyer une commande au véhicule
    Le serveur relaie au client USB qui l'envoie via série
    """
    global state
    
    if not state.usb_client_connected:
        emit('error', {'message': 'Client USB non connecté'})
        return
    
    if not state.vehicle_connected:
        emit('error', {'message': 'Véhicule non connecté'})
        return
    
    try:
        # Créer la commande au format attendu
        command = {
            'direction': data.get('direction', 1500),
            'throttle': data.get('throttle', 1500),
            'mode': data.get('mode', 'manual'),
            'timestamp': datetime.now().isoformat()
        }
        
        # Envoyer au client USB (qui va l'envoyer via série)
        socketio.emit('vehicle_command', command, room=state.usb_client_sid)
        
        state.commands_sent += 1
        logger.debug(f"Commande envoyée: DIR={command['direction']} THR={command['throttle']}")
        
        emit('command_sent', {'status': 'ok', 'command': command})
        
    except Exception as e:
        logger.error(f"Erreur envoi commande: {e}")
        emit('error', {'message': str(e)})

@socketio.on('quick_command')
def handle_quick_command(data):
    """
    Commandes rapides (avant, arrière, gauche, droite, stop)
    """
    cmd_type = data.get('command', 'stop')
    
    # Mapping des commandes
    commands = {
        'forward': {'direction': 1500, 'throttle': 1650},
        'backward': {'direction': 1500, 'throttle': 1350},
        'left': {'direction': 1300, 'throttle': 1500},
        'right': {'direction': 1700, 'throttle': 1500},
        'stop': {'direction': 1500, 'throttle': 1500},
        'center': {'direction': 1500, 'throttle': 1500}
    }
    
    if cmd_type in commands:
        handle_send_command(commands[cmd_type])
    else:
        emit('error', {'message': f'Commande inconnue: {cmd_type}'})

@socketio.on('ping')
def handle_ping():
    """Keepalive"""
    emit('pong', {'timestamp': datetime.now().isoformat()})

# ==================== Gestion Véhicules ====================

@socketio.on('select_vehicle')
def handle_select_vehicle(data):
    """Sélectionner un véhicule"""
    vehicle_id = data.get('vehicle_id')
    
    if not state.usb_client_connected:
        emit('error', {'message': 'Client USB non connecté'})
        return
    
    # Demander au client USB de se connecter à ce véhicule
    socketio.emit('connect_vehicle', {
        'vehicle_id': vehicle_id
    }, room=state.usb_client_sid)
    
    logger.info(f"Demande de connexion au véhicule: {vehicle_id}")

# ==================== Lancement ====================

def print_banner():
    """Affiche la bannière de démarrage"""
    print("\n" + "=" * 70)
    print("  🚗 CyberDrive - Web Server (Version Proxmox)")
    print("=" * 70)
    print(f"  Interface Web: http://0.0.0.0:5000")
    print(f"  API Status:    http://0.0.0.0:5000/api/status")
    print(f"  Démarré:       {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print("\n  Attente des connexions...")
    print("    - Clients web (navigateur)")
    print("    - Client USB (PC avec ESP32)")
    print("\n")

if __name__ == '__main__':
    print_banner()
    
    # Charger les configs
    vehicles = load_vehicle_configs()
    logger.info(f"Véhicules chargés: {len(vehicles)}")
    
    # Lancer le serveur
    try:
        socketio.run(
            app,
            host='0.0.0.0',  # Accessible depuis l'extérieur
            port=5000,
            debug=False,  # Mettre True pour dev
            allow_unsafe_werkzeug=True  # Pour dev uniquement
        )
    except KeyboardInterrupt:
        print("\n\n✓ Arrêt du serveur...")
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        raise
