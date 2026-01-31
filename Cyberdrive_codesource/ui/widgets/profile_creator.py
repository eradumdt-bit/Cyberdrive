"""
Profile Creator Widget - Create vehicle profiles without code
"""
from PyQt6.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, 
                              QLabel, QLineEdit, QComboBox, QSpinBox, 
                              QCheckBox, QPushButton, QTextEdit, QGroupBox,
                              QScrollArea, QMessageBox, QFileDialog, QListWidget,
                              QDoubleSpinBox, QTabWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from pathlib import Path
import json
from typing import List, Dict, Any


class ProfileCreatorDialog(QDialog):
    """Dialog for creating/editing vehicle profiles"""
    
    profile_saved = pyqtSignal(str)  # Emits the path to saved profile
    
    def __init__(self, parent=None, edit_profile_path: str = None):
        super().__init__(parent)
        self.edit_mode = edit_profile_path is not None
        self.edit_profile_path = edit_profile_path
        
        self.setWindowTitle("Create Vehicle Profile" if not self.edit_mode else "Edit Vehicle Profile")
        self.setMinimumSize(800, 700)
        
        self.setup_ui()
        
        if self.edit_mode:
            self.load_profile(edit_profile_path)
    
    def setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("🚗 Vehicle Profile Creator" if not self.edit_mode else "✏️ Edit Vehicle Profile")
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Scroll area for all fields
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)
        
        # === BASIC INFO ===
        basic_group = self._create_basic_info_group()
        scroll_layout.addWidget(basic_group)
        
        # === CONNECTION ===
        connection_group = self._create_connection_group()
        scroll_layout.addWidget(connection_group)
        
        # === CAPABILITIES ===
        capabilities_group = self._create_capabilities_group()
        scroll_layout.addWidget(capabilities_group)
        
        # === PROTOCOL ===
        protocol_group = self._create_protocol_group()
        scroll_layout.addWidget(protocol_group)
        
        # === LIMITS ===
        limits_group = self._create_limits_group()
        scroll_layout.addWidget(limits_group)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)
        
        # === BUTTONS ===
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Preview JSON button
        preview_btn = QPushButton("👁️ Preview JSON")
        preview_btn.clicked.connect(self.preview_json)
        button_layout.addWidget(preview_btn)
        
        button_layout.addStretch()
        
        # Cancel button
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        # Save button
        save_btn = QPushButton("💾 Save Profile")
        save_btn.setProperty("class", "primary")
        save_btn.clicked.connect(self.save_profile)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def _create_basic_info_group(self) -> QGroupBox:
        """Create basic information group"""
        group = QGroupBox("📋 Basic Information")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        # ID
        id_layout = QHBoxLayout()
        id_layout.addWidget(QLabel("Vehicle ID:"))
        self.id_edit = QLineEdit()
        self.id_edit.setPlaceholderText("e.g., rc_car_001")
        id_layout.addWidget(self.id_edit, 1)
        layout.addLayout(id_layout)
        
        # Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., RC Car Proto v1")
        name_layout.addWidget(self.name_edit, 1)
        layout.addLayout(name_layout)
        
        # Type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["rc_car", "drone", "robot", "real_car", "custom"])
        self.type_combo.setEditable(True)
        type_layout.addWidget(self.type_combo, 1)
        layout.addLayout(type_layout)
        
        # Description
        layout.addWidget(QLabel("Description:"))
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Brief description of the vehicle...")
        layout.addWidget(self.description_edit)
        
        return group
    
    def _create_connection_group(self) -> QGroupBox:
        """Create connection configuration group"""
        group = QGroupBox("🔌 Connection Configuration")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        # Preferred mode
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Preferred Mode:"))
        self.conn_mode_combo = QComboBox()
        self.conn_mode_combo.addItems(["serial", "wifi", "both"])
        self.conn_mode_combo.currentTextChanged.connect(self._update_connection_visibility)
        mode_layout.addWidget(self.conn_mode_combo, 1)
        layout.addLayout(mode_layout)
        
        # === SERIAL ===
        self.serial_group = QGroupBox("Serial Configuration")
        serial_layout = QVBoxLayout(self.serial_group)
        
        # Port
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Port:"))
        self.serial_port_edit = QLineEdit("AUTO")
        self.serial_port_edit.setPlaceholderText("AUTO or COM3, /dev/ttyUSB0, etc.")
        port_layout.addWidget(self.serial_port_edit, 1)
        serial_layout.addLayout(port_layout)
        
        # Baudrate
        baud_layout = QHBoxLayout()
        baud_layout.addWidget(QLabel("Baudrate:"))
        self.serial_baudrate_spin = QComboBox()
        self.serial_baudrate_spin.addItems(["9600", "19200", "38400", "57600", "115200", "230400"])
        self.serial_baudrate_spin.setCurrentText("115200")
        self.serial_baudrate_spin.setEditable(True)
        baud_layout.addWidget(self.serial_baudrate_spin, 1)
        serial_layout.addLayout(baud_layout)
        
        # Description
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Description:"))
        self.serial_desc_edit = QLineEdit("USB Connection")
        desc_layout.addWidget(self.serial_desc_edit, 1)
        serial_layout.addLayout(desc_layout)
        
        layout.addWidget(self.serial_group)
        
        # === WIFI ===
        self.wifi_group = QGroupBox("WiFi Configuration")
        wifi_layout = QVBoxLayout(self.wifi_group)
        
        # IP
        ip_layout = QHBoxLayout()
        ip_layout.addWidget(QLabel("IP Address:"))
        self.wifi_ip_edit = QLineEdit("192.168.1.50")
        self.wifi_ip_edit.setPlaceholderText("e.g., 192.168.1.100")
        ip_layout.addWidget(self.wifi_ip_edit, 1)
        wifi_layout.addLayout(ip_layout)
        
        # Port
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Port:"))
        self.wifi_port_spin = QSpinBox()
        self.wifi_port_spin.setRange(1, 65535)
        self.wifi_port_spin.setValue(8888)
        port_layout.addWidget(self.wifi_port_spin, 1)
        wifi_layout.addLayout(port_layout)
        
        # Enabled
        self.wifi_enabled_check = QCheckBox("WiFi Enabled")
        wifi_layout.addWidget(self.wifi_enabled_check)
        
        layout.addWidget(self.wifi_group)
        
        return group
    
    def _create_capabilities_group(self) -> QGroupBox:
        """Create capabilities group"""
        group = QGroupBox("⚙️ Capabilities")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        # Max Speed
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Max Speed (km/h):"))
        self.max_speed_spin = QDoubleSpinBox()
        self.max_speed_spin.setRange(0, 500)
        self.max_speed_spin.setValue(30)
        self.max_speed_spin.setSuffix(" km/h")
        speed_layout.addWidget(self.max_speed_spin, 1)
        layout.addLayout(speed_layout)
        
        # Has camera
        self.has_camera_check = QCheckBox("Has Onboard Camera")
        layout.addWidget(self.has_camera_check)
        
        # Sensors
        layout.addWidget(QLabel("Sensors (one per line):"))
        self.sensors_list = QTextEdit()
        self.sensors_list.setMaximumHeight(100)
        self.sensors_list.setPlaceholderText("ultrasonic_hcsr04\nmpu6500\nbattery_voltage")
        layout.addWidget(self.sensors_list)
        
        # Actuators
        layout.addWidget(QLabel("Actuators (one per line):"))
        self.actuators_list = QTextEdit()
        self.actuators_list.setMaximumHeight(100)
        self.actuators_list.setPlaceholderText("servo_steering\nesc_throttle\nled_indicators")
        layout.addWidget(self.actuators_list)
        
        return group
    
    def _create_protocol_group(self) -> QGroupBox:
        """Create protocol group"""
        group = QGroupBox("📡 Protocol")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        # Version
        ver_layout = QHBoxLayout()
        ver_layout.addWidget(QLabel("Version:"))
        self.protocol_version_edit = QLineEdit("esp32_v1")
        self.protocol_version_edit.setPlaceholderText("e.g., esp32_v1, arduino_v2")
        ver_layout.addWidget(self.protocol_version_edit, 1)
        layout.addLayout(ver_layout)
        
        # Command format
        layout.addWidget(QLabel("Command Format:"))
        self.cmd_format_edit = QLineEdit("CMD:MOVE:{dir}:{thr}\\n")
        self.cmd_format_edit.setPlaceholderText("Use {dir}, {thr} as placeholders")
        layout.addWidget(self.cmd_format_edit)
        
        hint = QLabel("💡 Tip: {dir} = direction, {thr} = throttle, \\n = newline")
        hint.setStyleSheet("color: #888; font-size: 9pt;")
        layout.addWidget(hint)
        
        # Telemetry format
        layout.addWidget(QLabel("Telemetry Format:"))
        self.telem_format_edit = QLineEdit("TELEM:{dir}:{thr}:{dist}:{batt}:{rx}\\n")
        self.telem_format_edit.setPlaceholderText("Expected telemetry response format")
        layout.addWidget(self.telem_format_edit)
        
        return group
    
    def _create_limits_group(self) -> QGroupBox:
        """Create limits/calibration group"""
        group = QGroupBox("📏 Control Limits")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        info = QLabel("⚠️ PWM values typically range from 1000 to 2000 (µs)")
        info.setStyleSheet("color: #ffa500; font-size: 9pt;")
        layout.addWidget(info)
        
        # Direction limits
        dir_label = QLabel("Direction (Steering):")
        dir_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(dir_label)
        
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Min:"))
        self.dir_min_spin = QSpinBox()
        self.dir_min_spin.setRange(500, 2500)
        self.dir_min_spin.setValue(1000)
        dir_layout.addWidget(self.dir_min_spin)
        
        dir_layout.addWidget(QLabel("Center:"))
        self.dir_center_spin = QSpinBox()
        self.dir_center_spin.setRange(500, 2500)
        self.dir_center_spin.setValue(1500)
        dir_layout.addWidget(self.dir_center_spin)
        
        dir_layout.addWidget(QLabel("Max:"))
        self.dir_max_spin = QSpinBox()
        self.dir_max_spin.setRange(500, 2500)
        self.dir_max_spin.setValue(2000)
        dir_layout.addWidget(self.dir_max_spin)
        layout.addLayout(dir_layout)
        
        # Throttle limits
        thr_label = QLabel("Throttle (Speed):")
        thr_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(thr_label)
        
        thr_layout = QHBoxLayout()
        thr_layout.addWidget(QLabel("Min:"))
        self.thr_min_spin = QSpinBox()
        self.thr_min_spin.setRange(500, 2500)
        self.thr_min_spin.setValue(1000)
        thr_layout.addWidget(self.thr_min_spin)
        
        thr_layout.addWidget(QLabel("Neutral:"))
        self.thr_neutral_spin = QSpinBox()
        self.thr_neutral_spin.setRange(500, 2500)
        self.thr_neutral_spin.setValue(1500)
        thr_layout.addWidget(self.thr_neutral_spin)
        
        thr_layout.addWidget(QLabel("Max:"))
        self.thr_max_spin = QSpinBox()
        self.thr_max_spin.setRange(500, 2500)
        self.thr_max_spin.setValue(2000)
        thr_layout.addWidget(self.thr_max_spin)
        layout.addLayout(thr_layout)
        
        return group
    
    def _update_connection_visibility(self, mode: str):
        """Update visibility of connection groups based on mode"""
        self.serial_group.setVisible(mode in ["serial", "both"])
        self.wifi_group.setVisible(mode in ["wifi", "both"])
    
    def _get_list_items(self, text_edit: QTextEdit) -> List[str]:
        """Convert text edit content to list of items"""
        text = text_edit.toPlainText().strip()
        if not text:
            return []
        return [line.strip() for line in text.split('\n') if line.strip()]
    
    def build_profile_dict(self) -> Dict[str, Any]:
        """Build profile dictionary from UI fields"""
        profile = {
            "id": self.id_edit.text().strip(),
            "name": self.name_edit.text().strip(),
            "type": self.type_combo.currentText().strip(),
            "description": self.description_edit.toPlainText().strip(),
            
            "connection": {
                "preferred_mode": self.conn_mode_combo.currentText(),
                "serial": {
                    "port": self.serial_port_edit.text().strip(),
                    "baudrate": int(self.serial_baudrate_spin.currentText()),
                    "description": self.serial_desc_edit.text().strip()
                },
                "wifi": {
                    "ip": self.wifi_ip_edit.text().strip(),
                    "port": self.wifi_port_spin.value(),
                    "enabled": self.wifi_enabled_check.isChecked()
                }
            },
            
            "capabilities": {
                "max_speed_kmh": self.max_speed_spin.value(),
                "has_camera_onboard": self.has_camera_check.isChecked(),
                "sensors": self._get_list_items(self.sensors_list),
                "actuators": self._get_list_items(self.actuators_list)
            },
            
            "protocol": {
                "version": self.protocol_version_edit.text().strip(),
                "command_format": self.cmd_format_edit.text().strip(),
                "telemetry_format": self.telem_format_edit.text().strip()
            },
            
            "limits": {
                "dir_min": self.dir_min_spin.value(),
                "dir_max": self.dir_max_spin.value(),
                "dir_center": self.dir_center_spin.value(),
                "thr_min": self.thr_min_spin.value(),
                "thr_max": self.thr_max_spin.value(),
                "thr_neutral": self.thr_neutral_spin.value()
            }
        }
        
        return profile
    
    def validate_profile(self, profile: Dict[str, Any]) -> tuple[bool, str]:
        """Validate profile data"""
        if not profile["id"]:
            return False, "Vehicle ID is required"
        
        if not profile["name"]:
            return False, "Vehicle name is required"
        
        if not profile["type"]:
            return False, "Vehicle type is required"
        
        # Validate limits
        limits = profile["limits"]
        if limits["dir_min"] >= limits["dir_max"]:
            return False, "Direction min must be < max"
        
        if limits["thr_min"] >= limits["thr_max"]:
            return False, "Throttle min must be < max"
        
        return True, ""
    
    def preview_json(self):
        """Preview the JSON that will be saved"""
        try:
            profile = self.build_profile_dict()
            json_str = json.dumps(profile, indent=2)
            
            # Create preview dialog
            preview = QDialog(self)
            preview.setWindowTitle("JSON Preview")
            preview.setMinimumSize(600, 500)
            
            layout = QVBoxLayout(preview)
            
            text_edit = QTextEdit()
            text_edit.setPlainText(json_str)
            text_edit.setReadOnly(True)
            text_edit.setStyleSheet("font-family: 'Courier New', monospace;")
            layout.addWidget(text_edit)
            
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(preview.accept)
            layout.addWidget(close_btn)
            
            preview.exec()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to generate JSON:\n{str(e)}")
    
    def save_profile(self):
        """Save profile to JSON file"""
        try:
            # Build and validate profile
            profile = self.build_profile_dict()
            valid, error = self.validate_profile(profile)
            
            if not valid:
                QMessageBox.warning(self, "Validation Error", error)
                return
            
            # Get save path
            if self.edit_mode:
                file_path = self.edit_profile_path
            else:
                default_name = f"{profile['id']}.json"
                config_dir = Path(__file__).parent.parent.parent / "config" / "vehicles"
                config_dir.mkdir(parents=True, exist_ok=True)
                
                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Save Vehicle Profile",
                    str(config_dir / default_name),
                    "JSON Files (*.json)"
                )
            
            if not file_path:
                return
            
            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2)
            
            QMessageBox.information(
                self, 
                "Success", 
                f"Profile saved successfully!\n\n{file_path}"
            )
            
            self.profile_saved.emit(file_path)
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save profile:\n{str(e)}")
    
    def load_profile(self, file_path: str):
        """Load existing profile for editing"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                profile = json.load(f)
            
            # Basic info
            self.id_edit.setText(profile.get("id", ""))
            self.name_edit.setText(profile.get("name", ""))
            self.type_combo.setCurrentText(profile.get("type", "rc_car"))
            self.description_edit.setPlainText(profile.get("description", ""))
            
            # Connection
            conn = profile.get("connection", {})
            self.conn_mode_combo.setCurrentText(conn.get("preferred_mode", "serial"))
            
            serial = conn.get("serial", {})
            self.serial_port_edit.setText(serial.get("port", "AUTO"))
            self.serial_baudrate_spin.setCurrentText(str(serial.get("baudrate", 115200)))
            self.serial_desc_edit.setText(serial.get("description", ""))
            
            wifi = conn.get("wifi", {})
            self.wifi_ip_edit.setText(wifi.get("ip", ""))
            self.wifi_port_spin.setValue(wifi.get("port", 8888))
            self.wifi_enabled_check.setChecked(wifi.get("enabled", False))
            
            # Capabilities
            cap = profile.get("capabilities", {})
            self.max_speed_spin.setValue(cap.get("max_speed_kmh", 30))
            self.has_camera_check.setChecked(cap.get("has_camera_onboard", False))
            
            sensors = cap.get("sensors", [])
            self.sensors_list.setPlainText('\n'.join(sensors))
            
            actuators = cap.get("actuators", [])
            self.actuators_list.setPlainText('\n'.join(actuators))
            
            # Protocol
            proto = profile.get("protocol", {})
            self.protocol_version_edit.setText(proto.get("version", ""))
            self.cmd_format_edit.setText(proto.get("command_format", ""))
            self.telem_format_edit.setText(proto.get("telemetry_format", ""))
            
            # Limits
            limits = profile.get("limits", {})
            self.dir_min_spin.setValue(limits.get("dir_min", 1000))
            self.dir_max_spin.setValue(limits.get("dir_max", 2000))
            self.dir_center_spin.setValue(limits.get("dir_center", 1500))
            self.thr_min_spin.setValue(limits.get("thr_min", 1000))
            self.thr_max_spin.setValue(limits.get("thr_max", 2000))
            self.thr_neutral_spin.setValue(limits.get("thr_neutral", 1500))
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load profile:\n{str(e)}")