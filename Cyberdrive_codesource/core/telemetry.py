"""
Telemetry data structures
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

@dataclass
class VehicleTelemetry:
    """Vehicle telemetry data"""
    
    # Timestamp
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Control values (PWM microseconds)
    direction: int = 1500  # 1000-2000 µs
    throttle: int = 1500   # 1000-2000 µs
    
    # Sensors
    distance_cm: int = -1  # -1 = no reading
    battery_voltage: float = 0.0
    
    # Status
    rx_active: bool = False  # RC receiver signal present
    obstacle_detected: bool = False
    mode: str = "unknown"  # rc, manual, auto
    
    # IMU (if available)
    accel_x: Optional[int] = None
    accel_y: Optional[int] = None
    accel_z: Optional[int] = None
    gyro_x: Optional[int] = None
    gyro_y: Optional[int] = None
    gyro_z: Optional[int] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'direction': self.direction,
            'throttle': self.throttle,
            'distance_cm': self.distance_cm,
            'battery_voltage': self.battery_voltage,
            'rx_active': self.rx_active,
            'obstacle_detected': self.obstacle_detected,
            'mode': self.mode,
            'imu': {
                'accel': [self.accel_x, self.accel_y, self.accel_z],
                'gyro': [self.gyro_x, self.gyro_y, self.gyro_z]
            } if self.accel_x is not None else None
        }
    
    @classmethod
    def from_esp32_string(cls, data: str) -> 'VehicleTelemetry':
        """
        Parse ESP32 telemetry string
        Format: TELEM:{dir}:{thr}:{dist}:{batt}:{rx}\n
        Example: TELEM:1450:1520:45:11.2:1\n
        """
        try:
            parts = data.strip().split(':')
            if len(parts) >= 6 and parts[0] == 'TELEM':
                return cls(
                    direction=int(parts[1]),
                    throttle=int(parts[2]),
                    distance_cm=int(parts[3]),
                    battery_voltage=float(parts[4]),
                    rx_active=bool(int(parts[5]))
                )
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid telemetry format: {data}") from e
        
        raise ValueError(f"Invalid telemetry format: {data}")

@dataclass
class VehicleCommand:
    """Command to send to vehicle"""
    
    direction: int = 1500  # 1000-2000 µs
    throttle: int = 1500   # 1000-2000 µs
    mode: str = "manual"   # manual, auto
    
    def to_esp32_string(self) -> str:
        """
        Convert to ESP32 command string
        Format: CMD:MOVE:{dir}:{thr}\n
        """
        return f"CMD:MOVE:{self.direction}:{self.throttle}\n"
    
    def validate(self, limits: dict) -> bool:
        """Validate command against vehicle limits"""
        dir_min = limits.get('dir_min', 1000)
        dir_max = limits.get('dir_max', 2000)
        thr_min = limits.get('thr_min', 1000)
        thr_max = limits.get('thr_max', 2000)
        
        if not (dir_min <= self.direction <= dir_max):
            return False
        if not (thr_min <= self.throttle <= thr_max):
            return False
        
        return True