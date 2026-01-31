"""
Vehicle manager - handles multiple vehicles and their connections
"""
from typing import Optional, List, Dict
from pathlib import Path
from .vehicle_profile import VehicleProfile
from .adapters.base_adapter import BaseAdapter
from .adapters.serial_adapter import SerialAdapter
from .adapters.wifi_adapter import WiFiAdapter
from core.telemetry import VehicleTelemetry, VehicleCommand
from utils.logger import get_logger

logger = get_logger()

class VehicleManager:
    """Manage multiple vehicles and their connections"""
    
    def __init__(self):
        self._vehicles: Dict[str, VehicleProfile] = {}
        self._adapters: Dict[str, BaseAdapter] = {}
        self._active_vehicle_id: Optional[str] = None
    
    def load_vehicle_profiles(self, config_dir: str | Path):
        """
        Load all vehicle profiles from config directory
        
        Args:
            config_dir: Path to config/vehicles directory
        """
        config_path = Path(config_dir)
        
        if not config_path.exists():
            logger.warning(f"Vehicle config directory not found: {config_path}")
            return
        
        # Load all JSON files
        for json_file in config_path.glob("*.json"):
            try:
                profile = VehicleProfile.from_json_file(json_file)
                self._vehicles[profile.id] = profile
                logger.info(f"Loaded vehicle profile: {profile.name} ({profile.id})")
            except Exception as e:
                logger.error(f"Failed to load {json_file}: {e}")
    
    def get_vehicle_list(self) -> List[VehicleProfile]:
        """Get list of all loaded vehicles"""
        return list(self._vehicles.values())
    
    def get_vehicle(self, vehicle_id: str) -> Optional[VehicleProfile]:
        """Get vehicle profile by ID"""
        return self._vehicles.get(vehicle_id)
    
    def connect_vehicle(self, vehicle_id: str) -> bool:
        """
        Connect to a vehicle
        
        Args:
            vehicle_id: Vehicle ID to connect
            
        Returns:
            True if connection successful
        """
        vehicle = self._vehicles.get(vehicle_id)
        if not vehicle:
            logger.error(f"Vehicle not found: {vehicle_id}")
            return False
        
        # Disconnect previous vehicle if any
        if self._active_vehicle_id:
            self.disconnect_vehicle(self._active_vehicle_id)
        
        # Create appropriate adapter
        conn = vehicle.connection
        adapter: Optional[BaseAdapter] = None
        
        if conn.preferred_mode == "serial":
            adapter = SerialAdapter(
                port=conn.serial_port,
                baudrate=conn.serial_baudrate
            )
        elif conn.preferred_mode == "wifi" and conn.wifi_enabled:
            adapter = WiFiAdapter(
                ip=conn.wifi_ip,
                port=conn.wifi_port
            )
        else:
            logger.error(f"Invalid connection mode: {conn.preferred_mode}")
            return False
        
        # Attempt connection
        if adapter.connect():
            self._adapters[vehicle_id] = adapter
            self._active_vehicle_id = vehicle_id
            logger.info(f"✓ Vehicle connected: {vehicle.name}")
            return True
        else:
            logger.error(f"✗ Failed to connect vehicle: {vehicle.name}")
            return False
    
    def disconnect_vehicle(self, vehicle_id: str):
        """Disconnect a vehicle"""
        adapter = self._adapters.get(vehicle_id)
        if adapter:
            adapter.disconnect()
            del self._adapters[vehicle_id]
            
            if self._active_vehicle_id == vehicle_id:
                self._active_vehicle_id = None
            
            logger.info(f"Vehicle disconnected: {vehicle_id}")
    
    def send_command(self, command: VehicleCommand, vehicle_id: Optional[str] = None) -> bool:
        """
        Send command to vehicle
        
        Args:
            command: VehicleCommand object
            vehicle_id: Target vehicle ID (uses active if None)
            
        Returns:
            True if command sent successfully
        """
        target_id = vehicle_id or self._active_vehicle_id
        
        if not target_id:
            logger.warning("No active vehicle to send command")
            return False
        
        adapter = self._adapters.get(target_id)
        vehicle = self._vehicles.get(target_id)
        
        if not adapter or not vehicle:
            return False
        
        # Validate command against vehicle limits
        if not command.validate(vehicle.limits):
            logger.warning(f"Command validation failed: {command}")
            return False
        
        return adapter.send_command(command)
    
    def receive_telemetry(self, vehicle_id: Optional[str] = None) -> Optional[VehicleTelemetry]:
        """
        Receive telemetry from vehicle
        
        Args:
            vehicle_id: Target vehicle ID (uses active if None)
            
        Returns:
            VehicleTelemetry or None
        """
        target_id = vehicle_id or self._active_vehicle_id
        
        if not target_id:
            return None
        
        adapter = self._adapters.get(target_id)
        if adapter:
            return adapter.receive_telemetry()
        
        return None
    
    def get_active_vehicle(self) -> Optional[VehicleProfile]:
        """Get currently active vehicle profile"""
        if self._active_vehicle_id:
            return self._vehicles.get(self._active_vehicle_id)
        return None
    
    def is_vehicle_connected(self, vehicle_id: Optional[str] = None) -> bool:
        """Check if vehicle is connected"""
        target_id = vehicle_id or self._active_vehicle_id
        if target_id:
            adapter = self._adapters.get(target_id)
            return adapter.is_connected if adapter else False
        return False
    
    def get_connection_info(self, vehicle_id: Optional[str] = None) -> Optional[dict]:
        """Get connection information for vehicle"""
        target_id = vehicle_id or self._active_vehicle_id
        if target_id:
            adapter = self._adapters.get(target_id)
            return adapter.get_connection_info() if adapter else None
        return None