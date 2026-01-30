"""
Vehicle selector widget
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox
from PyQt6.QtCore import Qt, pyqtSignal
from typing import List
from vehicle.vehicle_profile import VehicleProfile

class VehicleSelector(QWidget):
    """Widget for selecting active vehicle"""
    
    # Signal emitted when vehicle selection changes
    vehicle_changed = pyqtSignal(str)  # vehicle_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._vehicles: List[VehicleProfile] = []
        self.setup_ui()
        
    def setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Label
        label = QLabel("Select Vehicle:")
        label.setProperty("class", "subtitle")
        layout.addWidget(label)
        
        # ComboBox
        self.combo = QComboBox()
        self.combo.currentIndexChanged.connect(self._on_selection_changed)
        layout.addWidget(self.combo)
        
        # Info label
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #a0a0a0; font-size: 9pt;")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
    
    def set_vehicles(self, vehicles: List[VehicleProfile]):
        """Set available vehicles"""
        self._vehicles = vehicles
        self.combo.clear()
        
        for vehicle in vehicles:
            display_text = f"{vehicle.name} ({vehicle.type})"
            self.combo.addItem(display_text, vehicle.id)
        
        if vehicles:
            self._update_info(0)
    
    def get_selected_vehicle_id(self) -> str:
        """Get currently selected vehicle ID"""
        return self.combo.currentData()
    
    def get_selected_vehicle(self) -> VehicleProfile:
        """Get currently selected vehicle profile"""
        vehicle_id = self.get_selected_vehicle_id()
        for vehicle in self._vehicles:
            if vehicle.id == vehicle_id:
                return vehicle
        return None
    
    def _on_selection_changed(self, index: int):
        """Handle selection change"""
        if index >= 0:
            self._update_info(index)
            vehicle_id = self.combo.itemData(index)
            self.vehicle_changed.emit(vehicle_id)
    
    def _update_info(self, index: int):
        """Update info label with vehicle details"""
        if index < 0 or index >= len(self._vehicles):
            self.info_label.setText("")
            return
        
        vehicle = self._vehicles[index]
        conn = vehicle.connection
        
        info_parts = []
        info_parts.append(f"Type: {vehicle.type}")
        
        if conn.preferred_mode == "serial":
            port = conn.serial_port if conn.serial_port != "AUTO" else "Auto-detect"
            info_parts.append(f"Connection: Serial ({port})")
        elif conn.preferred_mode == "wifi":
            info_parts.append(f"Connection: WiFi ({conn.wifi_ip}:{conn.wifi_port})")
        
        self.info_label.setText(" | ".join(info_parts))