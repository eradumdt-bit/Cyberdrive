"""
Main window for CyberDrive UI
"""
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                              QLabel, QStatusBar, QSplitter)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QKeyEvent
from pathlib import Path

from ui.widgets.vehicle_selector import VehicleSelector
from ui.widgets.connection_widget import ConnectionWidget
from ui.widgets.telemetry_panel import TelemetryPanel
from ui.widgets.camera_grid import CameraGrid
from vehicle.vehicle_manager import VehicleManager
from core.telemetry import VehicleCommand
from camera.camera_manager import CameraManager
from utils.logger import get_logger

logger = get_logger()

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, vehicle_manager: VehicleManager):
        super().__init__()
        self.vehicle_manager = vehicle_manager
        self.camera_manager = CameraManager()
        
        self.telemetry_timer = QTimer()
        self.camera_timer = QTimer()
        self.heartbeat_timer = QTimer()  # Nouveau : heartbeat
        
        # Keyboard control state
        self.current_dir = 1500
        self.current_thr = 1500
        self.keys_pressed = set()
        
        # Control mode
        self.manual_control_active = False
        
        self.setup_ui()
        self.load_stylesheet()
        self.setup_connections()
        self.load_vehicles()
        self.init_cameras()
        
    def setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle("CyberDrive Control Server")
        self.setMinimumSize(1200, 800)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Left panel (controls)
        left_panel = QWidget()
        left_panel.setMaximumWidth(350)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(15)
        
        # Title
        title = QLabel("CYBERDRIVE")
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(title)
        
        # Vehicle selector
        self.vehicle_selector = VehicleSelector()
        left_layout.addWidget(self.vehicle_selector)
        
        # Connection widget
        self.connection_widget = ConnectionWidget()
        left_layout.addWidget(self.connection_widget)
        
        # Telemetry panel
        self.telemetry_panel = TelemetryPanel()
        left_layout.addWidget(self.telemetry_panel)
        
        # Control instructions
        control_label = QLabel(
            "<b>Keyboard Control:</b><br>"
            "Z = Forward<br>"
            "S = Backward<br>"
            "Q = Left<br>"
            "D = Right<br>"
            "Space = Stop"
        )
        control_label.setStyleSheet("color: #a0a0a0; font-size: 9pt;")
        left_layout.addWidget(control_label)
        
        left_layout.addStretch()
        
        # Right panel (cameras)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        cam_title = QLabel("CAMERA FEEDS")
        cam_title.setProperty("class", "title")
        cam_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(cam_title)
        
        self.camera_grid = CameraGrid(2, 2)
        right_layout.addWidget(self.camera_grid)
        
        # Add panels to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, 1)  # Stretch factor
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
    def load_stylesheet(self):
        """Load QSS stylesheet"""
        style_path = Path(__file__).parent / "resources" / "styles.qss"
        if style_path.exists():
            with open(style_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
            logger.info("Loaded stylesheet")
        else:
            logger.warning(f"Stylesheet not found: {style_path}")
    
    def setup_connections(self):
        """Setup signal/slot connections"""
        self.connection_widget.connect_clicked.connect(self.on_connect)
        self.connection_widget.disconnect_clicked.connect(self.on_disconnect)
        
        # Telemetry timer (10 Hz)
        self.telemetry_timer.timeout.connect(self.update_telemetry)
        
        # Camera timer (30 Hz)
        self.camera_timer.timeout.connect(self.update_cameras)
        
        # Heartbeat timer (1 Hz) - envoie juste un ping
        self.heartbeat_timer.timeout.connect(self.send_heartbeat)
        
        # Camera source changes
        for widget in self.camera_grid.camera_widgets:
            widget.source_changed.connect(self.on_camera_source_changed)
    
    def init_cameras(self):
        """Initialize camera system"""
        # Scan for USB cameras
        self.camera_manager.refresh_sources()
        
        # Update grid with available sources
        sources = self.camera_manager.get_available_sources()
        self.camera_grid.set_available_sources(sources)
        
        logger.info(f"Camera system initialized with {len(sources)} source(s)")
        
        # Start camera update timer (30 FPS)
        self.camera_timer.start(33)  # ~30 Hz
    
    def on_camera_source_changed(self, slot_index: int, source_id: str):
        """Handle camera source selection"""
        widget = self.camera_grid.get_camera_widget(slot_index)
        
        if source_id is None:
            # Close camera if open
            if hasattr(widget, '_open_source_id') and widget._open_source_id:
                self.camera_manager.close_camera(widget._open_source_id)
                widget._open_source_id = None
            return
        
        # Close previous source if different
        if hasattr(widget, '_open_source_id') and widget._open_source_id:
            if widget._open_source_id != source_id:
                self.camera_manager.close_camera(widget._open_source_id)
        
        # Open new source
        success = self.camera_manager.open_camera(source_id)
        
        if success:
            widget._open_source_id = source_id
            logger.info(f"Camera slot {slot_index} connected to: {source_id}")
        else:
            widget.show_error("Failed to open camera")
            widget._open_source_id = None
    
    def update_cameras(self):
        """Update all camera displays"""
        for widget in self.camera_grid.camera_widgets:
            if hasattr(widget, '_open_source_id') and widget._open_source_id:
                frame = self.camera_manager.read_frame(widget._open_source_id)
                if frame is not None:
                    widget.update_frame(frame)
        
    def load_vehicles(self):
        """Load available vehicles"""
        vehicles = self.vehicle_manager.get_vehicle_list()
        self.vehicle_selector.set_vehicles(vehicles)
        logger.info(f"Loaded {len(vehicles)} vehicle(s)")
        
    def on_connect(self):
        """Handle connect button"""
        vehicle_id = self.vehicle_selector.get_selected_vehicle_id()
        if not vehicle_id:
            self.status_bar.showMessage("No vehicle selected", 3000)
            return
        
        self.connection_widget.set_connecting()
        self.status_bar.showMessage("Connecting...")
        
        # Connect in background (should be threaded in production)
        success = self.vehicle_manager.connect_vehicle(vehicle_id)
        
        if success:
            conn_info = self.vehicle_manager.get_connection_info()
            info_text = f"{conn_info['type']}: {conn_info.get('port', conn_info.get('ip', ''))}"
            self.connection_widget.set_connected(True, info_text)
            self.status_bar.showMessage("Connected successfully", 3000)
            
            # Start timers
            self.telemetry_timer.start(100)   # 10 Hz telemetry
            self.heartbeat_timer.start(500)   # 2 Hz heartbeat
            
            logger.info(f"Connected to vehicle: {vehicle_id}")
        else:
            self.connection_widget.set_connected(False)
            self.connection_widget.enable_button(True)
            self.status_bar.showMessage("Connection failed", 3000)
            logger.error("Connection failed")
    
    def on_disconnect(self):
        """Handle disconnect button"""
        # Stop timers first
        self.telemetry_timer.stop()
        self.heartbeat_timer.stop()
        
        # Send neutral command before disconnect
        vehicle_id = self.vehicle_selector.get_selected_vehicle_id()
        if vehicle_id and self.vehicle_manager.is_vehicle_connected():
            neutral_cmd = VehicleCommand(direction=1500, throttle=1500)
            self.vehicle_manager.send_command(neutral_cmd)
            self.vehicle_manager.disconnect_vehicle(vehicle_id)
        
        # Update UI
        self.connection_widget.set_connected(False)
        self.connection_widget.enable_button(True)
        self.telemetry_panel.clear()
        self.status_bar.showMessage("Disconnected", 3000)
        
        # Reset keyboard control
        self.current_dir = 1500
        self.current_thr = 1500
        self.keys_pressed.clear()
        self.manual_control_active = False
        
        logger.info("Disconnected")
    
    def send_heartbeat(self):
        """Send heartbeat to vehicle to maintain connection"""
        if self.vehicle_manager.is_vehicle_connected():
            # Envoie PING pour maintenir la connexion
            try:
                adapter = self.vehicle_manager._adapters.get(
                    self.vehicle_manager._active_vehicle_id
                )
                if adapter and adapter._serial:
                    adapter._serial.write(b"PING\n")
            except:
                pass  # Ignore errors
    
    def update_telemetry(self):
        """Update telemetry display and send commands if needed"""
        # Receive telemetry
        telem = self.vehicle_manager.receive_telemetry()
        if telem:
            self.telemetry_panel.update_telemetry(telem)
        
        # Send commands ONLY if user is actively controlling
        if self.manual_control_active and self.vehicle_manager.is_vehicle_connected():
            cmd = VehicleCommand(
                direction=self.current_dir,
                throttle=self.current_thr
            )
            self.vehicle_manager.send_command(cmd)
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard press"""
        key = event.key()
        
        # Ignore if already pressed (auto-repeat)
        if key in self.keys_pressed:
            return
        
        self.keys_pressed.add(key)
        self.manual_control_active = True  # Activer contrôle manuel
        self.update_control_from_keyboard()
        
    def keyReleaseEvent(self, event: QKeyEvent):
        """Handle keyboard release"""
        key = event.key()
        self.keys_pressed.discard(key)
        
        # Si plus aucune touche appuyée, retour neutre et désactiver contrôle
        if not self.keys_pressed:
            self.current_dir = 1500
            self.current_thr = 1500
            self.manual_control_active = False
        else:
            self.update_control_from_keyboard()
    
    def update_control_from_keyboard(self):
        """Update control values based on pressed keys"""
        # Direction (Q = left, D = right)
        if Qt.Key.Key_Q in self.keys_pressed:
            self.current_dir = 1200  # Left
        elif Qt.Key.Key_D in self.keys_pressed:
            self.current_dir = 1800  # Right
        else:
            self.current_dir = 1500  # Center
        
        # Throttle (Z = forward, S = backward)
        if Qt.Key.Key_Z in self.keys_pressed:
            self.current_thr = 1700  # Forward
        elif Qt.Key.Key_S in self.keys_pressed:
            self.current_thr = 1300  # Backward
        elif Qt.Key.Key_Space in self.keys_pressed:
            self.current_thr = 1500  # Stop
        else:
            if Qt.Key.Key_Z not in self.keys_pressed and Qt.Key.Key_S not in self.keys_pressed:
                self.current_thr = 1500  # Neutral
    
    def closeEvent(self, event):
        """Handle window close"""
        # Stop timers
        self.telemetry_timer.stop()
        self.camera_timer.stop()
        self.heartbeat_timer.stop()
        
        # Close all cameras
        self.camera_manager.close_all()
        
        # Disconnect vehicle
        if self.vehicle_manager.is_vehicle_connected():
            vehicle_id = self.vehicle_selector.get_selected_vehicle_id()
            if vehicle_id:
                self.vehicle_manager.disconnect_vehicle(vehicle_id)
        
        event.accept()