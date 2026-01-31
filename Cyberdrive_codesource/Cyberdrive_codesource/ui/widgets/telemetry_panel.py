"""
Telemetry panel widget - displays real-time vehicle data
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QProgressBar, QFrame, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont
from core.telemetry import VehicleTelemetry

class TelemetryPanel(QWidget):
    """Widget displaying vehicle telemetry"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("TELEMETRY")
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Grid layout for values
        grid = QGridLayout()
        grid.setSpacing(15)
        
        # Direction value
        dir_label = QLabel("Direction")
        dir_label.setProperty("class", "subtitle")
        self.dir_value = QLabel("1500 µs")
        self.dir_value.setProperty("class", "value")
        self.dir_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(dir_label, 0, 0)
        grid.addWidget(self.dir_value, 1, 0)
        
        # Throttle value
        thr_label = QLabel("Throttle")
        thr_label.setProperty("class", "subtitle")
        self.thr_value = QLabel("1500 µs")
        self.thr_value.setProperty("class", "value")
        self.thr_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(thr_label, 0, 1)
        grid.addWidget(self.thr_value, 1, 1)
        
        layout.addLayout(grid)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # Distance
        dist_layout = QVBoxLayout()
        dist_label = QLabel("Distance")
        dist_label.setProperty("class", "subtitle")
        self.dist_value = QLabel("-- cm")
        self.dist_value.setProperty("class", "value")
        self.dist_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dist_layout.addWidget(dist_label)
        dist_layout.addWidget(self.dist_value)
        layout.addLayout(dist_layout)
        
        # Battery
        batt_layout = QVBoxLayout()
        batt_label = QLabel("Battery")
        batt_label.setProperty("class", "subtitle")
        self.batt_value = QLabel("0.0 V")
        self.batt_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.batt_value.setFont(font)
        
        self.batt_bar = QProgressBar()
        self.batt_bar.setRange(0, 100)
        self.batt_bar.setValue(0)
        self.batt_bar.setTextVisible(False)
        self.batt_bar.setMaximumHeight(20)
        
        batt_layout.addWidget(batt_label)
        batt_layout.addWidget(self.batt_value)
        batt_layout.addWidget(self.batt_bar)
        layout.addLayout(batt_layout)
        
        # RX Status
        rx_layout = QHBoxLayout()
        rx_label = QLabel("RC Receiver:")
        self.rx_status = QLabel("INACTIVE")
        self.rx_status.setProperty("class", "status-disconnected")
        rx_layout.addWidget(rx_label)
        rx_layout.addWidget(self.rx_status)
        rx_layout.addStretch()
        layout.addLayout(rx_layout)
        
        layout.addStretch()
    
    @pyqtSlot(object)
    def update_telemetry(self, telem: VehicleTelemetry):
        """Update displayed telemetry data"""
        
        # Direction
        self.dir_value.setText(f"{telem.direction} µs")
        
        # Throttle
        self.thr_value.setText(f"{telem.throttle} µs")
        
        # Distance
        if telem.distance_cm >= 0:
            self.dist_value.setText(f"{telem.distance_cm} cm")
            # Change color based on distance
            if telem.distance_cm < 20:
                self.dist_value.setStyleSheet("color: #ff4444;")
            elif telem.distance_cm < 50:
                self.dist_value.setStyleSheet("color: #ffaa00;")
            else:
                self.dist_value.setStyleSheet("color: #00ff88;")
        else:
            self.dist_value.setText("-- cm")
            self.dist_value.setStyleSheet("color: #a0a0a0;")
        
        # Battery
        self.batt_value.setText(f"{telem.battery_voltage:.1f} V")
        
        # Battery percentage (assume 9V-12.6V range for LiPo 3S)
        batt_percent = int(((telem.battery_voltage - 9.0) / 3.6) * 100)
        batt_percent = max(0, min(100, batt_percent))
        self.batt_bar.setValue(batt_percent)
        
        # Battery color
        if batt_percent > 50:
            self.batt_value.setStyleSheet("color: #00ff88;")
        elif batt_percent > 20:
            self.batt_value.setStyleSheet("color: #ffaa00;")
        else:
            self.batt_value.setStyleSheet("color: #ff4444;")
        
        # RX status
        if telem.rx_active:
            self.rx_status.setText("ACTIVE")
            self.rx_status.setProperty("class", "status-connected")
        else:
            self.rx_status.setText("INACTIVE")
            self.rx_status.setProperty("class", "status-disconnected")
        
        # Force style update
        self.rx_status.style().unpolish(self.rx_status)
        self.rx_status.style().polish(self.rx_status)
    
    def clear(self):
        """Clear all telemetry values"""
        self.dir_value.setText("-- µs")
        self.thr_value.setText("-- µs")
        self.dist_value.setText("-- cm")
        self.batt_value.setText("-- V")
        self.batt_bar.setValue(0)
        self.rx_status.setText("INACTIVE")
        self.rx_status.setProperty("class", "status-disconnected")