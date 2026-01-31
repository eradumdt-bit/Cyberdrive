"""
Connection control widget
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal

class ConnectionWidget(QWidget):
    """Widget for controlling vehicle connection"""
    
    # Signals
    connect_clicked = pyqtSignal()
    disconnect_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._connected = False
        self.setup_ui()
        
    def setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Status label
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))
        self.status_label = QLabel("DISCONNECTED")
        self.status_label.setProperty("class", "status-disconnected")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        # Connection info
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #a0a0a0; font-size: 9pt;")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        
        # Connect button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setProperty("class", "connect")
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        layout.addWidget(self.connect_btn)
        
    def _on_connect_clicked(self):
        """Handle connect/disconnect button click"""
        if self._connected:
            self.disconnect_clicked.emit()
        else:
            self.connect_clicked.emit()
    
    def set_connected(self, connected: bool, info: str = ""):
        """Update connection state"""
        self._connected = connected
        
        if connected:
            self.status_label.setText("CONNECTED")
            self.status_label.setProperty("class", "status-connected")
            self.connect_btn.setText("Disconnect")
            self.connect_btn.setProperty("class", "disconnect")
            self.info_label.setText(info)
        else:
            self.status_label.setText("DISCONNECTED")
            self.status_label.setProperty("class", "status-disconnected")
            self.connect_btn.setText("Connect")
            self.connect_btn.setProperty("class", "connect")
            self.info_label.setText("")
        
        # Force style update
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        self.connect_btn.style().unpolish(self.connect_btn)
        self.connect_btn.style().polish(self.connect_btn)
    
    def set_connecting(self):
        """Set connecting state"""
        self.status_label.setText("CONNECTING...")
        self.status_label.setProperty("class", "status-warning")
        self.connect_btn.setEnabled(False)
        
        # Force style update
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
    
    def enable_button(self, enabled: bool = True):
        """Enable/disable connect button"""
        self.connect_btn.setEnabled(enabled)