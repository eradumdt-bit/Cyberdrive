"""
Vehicle profile data structure
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any
from pathlib import Path
import json

@dataclass
class ConnectionConfig:
    """Vehicle connection configuration"""
    preferred_mode: str = "serial"  # serial, wifi, both
    
    # Serial config
    serial_port: str = "AUTO"
    serial_baudrate: int = 115200
    
    # WiFi config
    wifi_ip: str = ""
    wifi_port: int = 8888
    wifi_enabled: bool = False

@dataclass
class VehicleProfile:
    """Complete vehicle profile"""
    
    id: str
    name: str
    type: str  # rc_car, drone, real_car, etc.
    description: str = ""
    
    connection: ConnectionConfig = field(default_factory=ConnectionConfig)
    
    capabilities: Dict[str, Any] = field(default_factory=dict)
    protocol: Dict[str, Any] = field(default_factory=dict)
    limits: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_json_file(cls, file_path: str | Path) -> 'VehicleProfile':
        """Load vehicle profile from JSON file"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Vehicle profile not found: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Parse connection config
        conn_data = data.get('connection', {})
        connection = ConnectionConfig(
            preferred_mode=conn_data.get('preferred_mode', 'serial'),
            serial_port=conn_data.get('serial', {}).get('port', 'AUTO'),
            serial_baudrate=conn_data.get('serial', {}).get('baudrate', 115200),
            wifi_ip=conn_data.get('wifi', {}).get('ip', ''),
            wifi_port=conn_data.get('wifi', {}).get('port', 8888),
            wifi_enabled=conn_data.get('wifi', {}).get('enabled', False)
        )
        
        return cls(
            id=data['id'],
            name=data['name'],
            type=data['type'],
            description=data.get('description', ''),
            connection=connection,
            capabilities=data.get('capabilities', {}),
            protocol=data.get('protocol', {}),
            limits=data.get('limits', {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'description': self.description,
            'connection': {
                'preferred_mode': self.connection.preferred_mode,
                'serial': {
                    'port': self.connection.serial_port,
                    'baudrate': self.connection.serial_baudrate
                },
                'wifi': {
                    'ip': self.connection.wifi_ip,
                    'port': self.connection.wifi_port,
                    'enabled': self.connection.wifi_enabled
                }
            },
            'capabilities': self.capabilities,
            'protocol': self.protocol,
            'limits': self.limits
        }
    
    def save_to_file(self, file_path: str | Path):
        """Save profile to JSON file"""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)