"""
Vehicle selector widget with profile management
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QComboBox, QPushButton, QMenu, QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction
from typing import List
from pathlib import Path
from vehicle.vehicle_profile import VehicleProfile
from ui.widgets.profile_creator import ProfileCreatorDialog

class VehicleSelector(QWidget):
    """Widget for selecting active vehicle with profile management"""
    
    # Signals
    vehicle_changed = pyqtSignal(str)  # vehicle_id
    profiles_updated = pyqtSignal()    # Emitted when profiles need refresh
    
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
        
        # Selector and buttons row
        selector_layout = QHBoxLayout()
        selector_layout.setSpacing(5)
        
        # ComboBox
        self.combo = QComboBox()
        self.combo.currentIndexChanged.connect(self._on_selection_changed)
        selector_layout.addWidget(self.combo, 1)
        
        # Action buttons
        self.manage_btn = QPushButton("⚙️")
        self.manage_btn.setToolTip("Manage Profiles")
        self.manage_btn.setMaximumWidth(35)
        self.manage_btn.clicked.connect(self._show_manage_menu)
        selector_layout.addWidget(self.manage_btn)
        
        layout.addLayout(selector_layout)
        
        # Info label
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #a0a0a0; font-size: 9pt;")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
    
    def _show_manage_menu(self):
        """Show profile management menu"""
        menu = QMenu(self)
        
        # Create new profile
        create_action = QAction("➕ Create New Profile", self)
        create_action.triggered.connect(self._create_profile)
        menu.addAction(create_action)
        
        # Edit current profile
        edit_action = QAction("✏️ Edit Current Profile", self)
        edit_action.triggered.connect(self._edit_current_profile)
        edit_action.setEnabled(self.combo.count() > 0)
        menu.addAction(edit_action)
        
        menu.addSeparator()
        
        # Delete current profile
        delete_action = QAction("🗑️ Delete Current Profile", self)
        delete_action.triggered.connect(self._delete_current_profile)
        delete_action.setEnabled(self.combo.count() > 0)
        menu.addAction(delete_action)
        
        menu.addSeparator()
        
        # Refresh list
        refresh_action = QAction("🔄 Refresh List", self)
        refresh_action.triggered.connect(lambda: self.profiles_updated.emit())
        menu.addAction(refresh_action)
        
        # Show menu at button
        menu.exec(self.manage_btn.mapToGlobal(self.manage_btn.rect().bottomLeft()))
    
    def _create_profile(self):
        """Open dialog to create new profile"""
        dialog = ProfileCreatorDialog(self)
        dialog.profile_saved.connect(self._on_profile_saved)
        dialog.exec()
    
    def _edit_current_profile(self):
        """Edit the currently selected profile"""
        vehicle = self.get_selected_vehicle()
        if not vehicle:
            return
        
        # Find the profile file path
        config_dir = Path(__file__).parent.parent.parent / "config" / "vehicles"
        profile_path = config_dir / f"{vehicle.id}.json"
        
        if not profile_path.exists():
            QMessageBox.warning(
                self, 
                "File Not Found", 
                f"Profile file not found:\n{profile_path}"
            )
            return
        
        dialog = ProfileCreatorDialog(self, str(profile_path))
        dialog.profile_saved.connect(self._on_profile_saved)
        dialog.exec()
    
    def _delete_current_profile(self):
        """Delete the currently selected profile"""
        vehicle = self.get_selected_vehicle()
        if not vehicle:
            return
        
        reply = QMessageBox.question(
            self,
            "Delete Profile",
            f"Are you sure you want to delete:\n\n{vehicle.name} ({vehicle.id})\n\n"
            "This action cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                config_dir = Path(__file__).parent.parent.parent / "config" / "vehicles"
                profile_path = config_dir / f"{vehicle.id}.json"
                
                if profile_path.exists():
                    profile_path.unlink()
                    QMessageBox.information(self, "Success", "Profile deleted successfully!")
                    self.profiles_updated.emit()
                else:
                    QMessageBox.warning(self, "Error", "Profile file not found!")
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete profile:\n{str(e)}")
    
    def _on_profile_saved(self, file_path: str):
        """Handle profile saved signal"""
        # Emit signal to refresh vehicle list
        self.profiles_updated.emit()
    
    def set_vehicles(self, vehicles: List[VehicleProfile]):
        """Set available vehicles"""
        self._vehicles = vehicles
        current_id = self.combo.currentData()
        
        self.combo.clear()
        
        for vehicle in vehicles:
            display_text = f"{vehicle.name} ({vehicle.type})"
            self.combo.addItem(display_text, vehicle.id)
        
        # Try to restore previous selection
        if current_id:
            for i in range(self.combo.count()):
                if self.combo.itemData(i) == current_id:
                    self.combo.setCurrentIndex(i)
                    break
        
        if vehicles and self.combo.currentIndex() >= 0:
            self._update_info(self.combo.currentIndex())
    
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