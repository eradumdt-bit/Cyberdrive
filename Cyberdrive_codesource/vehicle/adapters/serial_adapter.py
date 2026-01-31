"""
Serial (COM port) adapter for vehicle communication
"""
import serial
import serial.tools.list_ports
from typing import Optional, List
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from .base_adapter import BaseAdapter
from core.telemetry import VehicleTelemetry, VehicleCommand
from utils.logger import get_logger

logger = get_logger()

class SerialAdapter(BaseAdapter):
    """Serial communication adapter (USB/COM port)"""
    
    def __init__(self, port: str = "AUTO", baudrate: int = 115200, timeout: float = 1.0):
        """
        Initialize serial adapter
        
        Args:
            port: COM port (e.g., "COM3") or "AUTO" for auto-detection
            baudrate: Serial baudrate
            timeout: Read timeout in seconds
        """
        super().__init__()
        self._port = port
        self._baudrate = baudrate
        self._timeout = timeout
        self._serial: Optional[serial.Serial] = None
    
    @staticmethod
    def list_available_ports() -> List[str]:
        """
        List all available COM ports
        
        Returns:
            List of port names
        """
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]
    
    @staticmethod
    def detect_esp32_port() -> Optional[str]:
        """
        Auto-detect ESP32 on COM ports
        
        Returns:
            Port name or None if not found
        """
        ports = serial.tools.list_ports.comports()
        
        # Common ESP32 identifiers
        esp32_identifiers = [
            "CP210",  # CP2102 USB bridge (common on ESP32)
            "CH340",  # CH340 USB bridge
            "FTDI",   # FTDI chips
            "USB-SERIAL",
            "Silicon Labs"
        ]
        
        for port in ports:
            description = port.description.upper()
            for identifier in esp32_identifiers:
                if identifier.upper() in description:
                    logger.info(f"Detected potential ESP32 on {port.device}: {port.description}")
                    return port.device
        
        return None
    
    def connect(self) -> bool:
        """Connect to serial port"""
        try:
            # Auto-detect port if needed
            if self._port == "AUTO":
                detected_port = self.detect_esp32_port()
                if detected_port:
                    self._port = detected_port
                    logger.info(f"Auto-detected port: {self._port}")
                else:
                    available = self.list_available_ports()
                    if available:
                        self._port = available[0]
                        logger.warning(f"No ESP32 detected, using first available port: {self._port}")
                    else:
                        logger.error("No COM ports available")
                        return False
            
            # Open serial connection
            self._serial = serial.Serial(
                port=self._port,
                baudrate=self._baudrate,
                timeout=self._timeout,
                write_timeout=self._timeout
            )
            
            # Flush buffers
            self._serial.reset_input_buffer()
            self._serial.reset_output_buffer()
            
            self._connected = True
            logger.info(f"✓ Connected to {self._port} at {self._baudrate} baud")
            return True
            
        except serial.SerialException as e:
            logger.error(f"✗ Failed to connect to {self._port}: {e}")
            self._connected = False
            return False
    
    def disconnect(self):
        """Disconnect from serial port"""
        if self._serial and self._serial.is_open:
            self._serial.close()
            self._connected = False
            logger.info(f"Disconnected from {self._port}")
    
    def send_command(self, command: VehicleCommand) -> bool:
        """Send command to vehicle via serial"""
        if not self._connected or not self._serial:
            logger.warning("Cannot send command: not connected")
            return False
        
        try:
            cmd_str = command.to_esp32_string()
            self._serial.write(cmd_str.encode('utf-8'))
            logger.debug(f"→ Sent: {cmd_str.strip()}")
            return True
            
        except serial.SerialException as e:
            logger.error(f"Failed to send command: {e}")
            self._connected = False
            return False
    
    def receive_telemetry(self) -> Optional[VehicleTelemetry]:
        """Receive telemetry from vehicle via serial"""
        if not self._connected or not self._serial:
            return None
        
        try:
            if self._serial.in_waiting > 0:
                line = self._serial.readline().decode('utf-8', errors='ignore').strip()
                
                if line:
                    # ===== DEBUG =====
                    print(f"DEBUG RAW: {line}")
                    # =================
                    
                    logger.debug(f"← Received: {line}")
                    
                    # Parse telemetry
                    if line.startswith("TELEM:"):
                        try:
                            telem = VehicleTelemetry.from_esp32_string(line)
                            self._last_telemetry = telem
                            return telem
                        except ValueError as e:
                            logger.warning(f"Invalid telemetry: {e}")
                    
                    # Handle other messages
                    elif line.startswith("ACK:") or line.startswith("HEARTBEAT:"):
                        logger.debug(f"Device message: {line}")
            
            return None
            
        except serial.SerialException as e:
            logger.error(f"Serial read error: {e}")
            self._connected = False
            return None
        except UnicodeDecodeError:
            # Ignore corrupted data
            return None
    
    def get_connection_info(self) -> dict:
        """Get connection information"""
        info = super().get_connection_info()
        info.update({
            'port': self._port,
            'baudrate': self._baudrate,
            'type': 'Serial'
        })
        return info