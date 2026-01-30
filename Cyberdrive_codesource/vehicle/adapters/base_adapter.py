"""
Base adapter interface for vehicle communication
"""
from abc import ABC, abstractmethod
from typing import Optional
import sys
from pathlib import Path

# Add project root to path if needed
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.telemetry import VehicleTelemetry, VehicleCommand

class BaseAdapter(ABC):
    """Abstract base class for vehicle communication adapters"""
    
    def __init__(self):
        self._connected = False
        self._last_telemetry: Optional[VehicleTelemetry] = None
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to vehicle
        
        Returns:
            True if connection successful
        """
        pass
    
    @abstractmethod
    def disconnect(self):
        """Close connection to vehicle"""
        pass
    
    @abstractmethod
    def send_command(self, command: VehicleCommand) -> bool:
        """
        Send command to vehicle
        
        Args:
            command: VehicleCommand object
            
        Returns:
            True if command sent successfully
        """
        pass
    
    @abstractmethod
    def receive_telemetry(self) -> Optional[VehicleTelemetry]:
        """
        Receive telemetry from vehicle
        
        Returns:
            VehicleTelemetry object or None if no data
        """
        pass
    
    @property
    def is_connected(self) -> bool:
        """Check if adapter is connected"""
        return self._connected
    
    @property
    def last_telemetry(self) -> Optional[VehicleTelemetry]:
        """Get last received telemetry"""
        return self._last_telemetry
    
    def get_connection_info(self) -> dict:
        """Get connection information"""
        return {
            'connected': self._connected,
            'type': self.__class__.__name__
        }