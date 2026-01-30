"""
WiFi/TCP adapter for vehicle communication
"""
import socket
from typing import Optional
from .base_adapter import BaseAdapter
from core.telemetry import VehicleTelemetry, VehicleCommand
from utils.logger import get_logger

logger = get_logger()

class WiFiAdapter(BaseAdapter):
    """WiFi/TCP communication adapter"""
    
    def __init__(self, ip: str, port: int = 8888, timeout: float = 5.0):
        """
        Initialize WiFi adapter
        
        Args:
            ip: ESP32 IP address
            port: TCP port
            timeout: Connection timeout in seconds
        """
        super().__init__()
        self._ip = ip
        self._port = port
        self._timeout = timeout
        self._socket: Optional[socket.socket] = None
        self._buffer = ""
    
    def connect(self) -> bool:
        """Connect to vehicle via TCP"""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(self._timeout)
            self._socket.connect((self._ip, self._port))
            
            # Set to non-blocking after connection
            self._socket.setblocking(False)
            
            self._connected = True
            logger.info(f"✓ Connected to {self._ip}:{self._port} via WiFi")
            return True
            
        except socket.timeout:
            logger.error(f"✗ Connection timeout to {self._ip}:{self._port}")
            self._connected = False
            return False
        except socket.error as e:
            logger.error(f"✗ Failed to connect to {self._ip}:{self._port}: {e}")
            self._connected = False
            return False
    
    def disconnect(self):
        """Disconnect from vehicle"""
        if self._socket:
            try:
                self._socket.close()
            except:
                pass
            self._socket = None
            self._connected = False
            logger.info(f"Disconnected from {self._ip}:{self._port}")
    
    def send_command(self, command: VehicleCommand) -> bool:
        """Send command to vehicle via WiFi"""
        if not self._connected or not self._socket:
            logger.warning("Cannot send command: not connected")
            return False
        
        try:
            cmd_str = command.to_esp32_string()
            self._socket.sendall(cmd_str.encode('utf-8'))
            logger.debug(f"→ Sent: {cmd_str.strip()}")
            return True
            
        except socket.error as e:
            logger.error(f"Failed to send command: {e}")
            self._connected = False
            return False
    
    def receive_telemetry(self) -> Optional[VehicleTelemetry]:
        """Receive telemetry from vehicle via WiFi"""
        if not self._connected or not self._socket:
            return None
        
        try:
            # Non-blocking receive
            data = self._socket.recv(1024).decode('utf-8', errors='ignore')
            
            if data:
                # Add to buffer
                self._buffer += data
                
                # Process complete lines
                while '\n' in self._buffer:
                    line, self._buffer = self._buffer.split('\n', 1)
                    line = line.strip()
                    
                    if line:
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
            
        except BlockingIOError:
            # No data available (normal for non-blocking socket)
            return None
        except socket.error as e:
            logger.error(f"Socket error: {e}")
            self._connected = False
            return None
    
    def get_connection_info(self) -> dict:
        """Get connection information"""
        info = super().get_connection_info()
        info.update({
            'ip': self._ip,
            'port': self._port,
            'type': 'WiFi'
        })
        return info