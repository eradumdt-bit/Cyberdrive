"""
Camera grid widget with source selection
"""
from PyQt6.QtWidgets import (QWidget, QGridLayout, QLabel, QFrame, QVBoxLayout, 
                              QComboBox, QPushButton, QHBoxLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QImage, QPixmap
import numpy as np

class CameraWidget(QFrame):
    """Single camera display widget with source selector"""
    
    source_changed = pyqtSignal(int, str)  # slot_index, source_id
    
    def __init__(self, slot_index: int, parent=None):
        super().__init__(parent)
        self.slot_index = slot_index
        self.current_source_id = None
        self.setup_ui()
        
    def setup_ui(self):
        """Setup user interface"""
        self.setFrameShape(QFrame.Shape.Box)
        self.setLineWidth(1)
        self.setStyleSheet("background-color: #1a1a1a; border: 1px solid #3d3d3d;")
        self.setMinimumSize(320, 240)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Top bar: source selector
        top_bar = QHBoxLayout()
        
        self.source_combo = QComboBox()
        self.source_combo.addItem("-- No feed --", None)
        self.source_combo.currentIndexChanged.connect(self._on_source_changed)
        top_bar.addWidget(self.source_combo)
        
        layout.addLayout(top_bar)
        
        # Video display
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("background-color: #0a0a0a; border: none;")
        self.video_label.setMinimumHeight(180)
        self.video_label.setText("📷\nNo feed")
        layout.addWidget(self.video_label, 1)
        
        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #666666; font-size: 9pt;")
        layout.addWidget(self.status_label)
    
    def set_available_sources(self, sources: list):
        """Set available camera sources"""
        current_text = self.source_combo.currentText()
        
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        self.source_combo.addItem("-- No feed --", None)
        
        for source in sources:
            display_text = f"{source.name} ({source.type})"
            self.source_combo.addItem(display_text, source.id)
        
        # Try to restore previous selection
        idx = self.source_combo.findText(current_text)
        if idx >= 0:
            self.source_combo.setCurrentIndex(idx)
        
        self.source_combo.blockSignals(False)
    
    def _on_source_changed(self, index: int):
        """Handle source selection change"""
        source_id = self.source_combo.currentData()
        self.current_source_id = source_id
        
        if source_id is None:
            self.video_label.clear()
            self.video_label.setText("📷\nNo feed")
            self.status_label.setText("No feed selected")
        else:
            self.status_label.setText(f"Opening: {self.source_combo.currentText()}")
        
        self.source_changed.emit(self.slot_index, source_id)
    
    def update_frame(self, frame: np.ndarray):
        """Update displayed frame"""
        if frame is None:
            return
        
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Get widget size
        widget_width = self.video_label.width()
        widget_height = self.video_label.height()
        
        # Resize frame to fit (maintain aspect ratio)
        h, w = rgb_frame.shape[:2]
        aspect = w / h
        
        if widget_width / widget_height > aspect:
            new_height = widget_height
            new_width = int(new_height * aspect)
        else:
            new_width = widget_width
            new_height = int(new_width / aspect)
        
        # Resize
        resized = cv2.resize(rgb_frame, (new_width, new_height))
        
        # Convert to QImage
        h, w, ch = resized.shape
        bytes_per_line = ch * w
        q_img = QImage(resized.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        
        # Display
        pixmap = QPixmap.fromImage(q_img)
        self.video_label.setPixmap(pixmap)
        
        self.status_label.setText(f"Live • {w}x{h}")
    
    def show_error(self, message: str):
        """Show error message"""
        self.video_label.clear()
        self.video_label.setText(f"❌\n{message}")
        self.status_label.setText("Error")

class CameraGrid(QWidget):
    """Widget displaying camera feeds in grid layout"""
    
    def __init__(self, rows: int = 2, cols: int = 2, parent=None):
        super().__init__(parent)
        self.rows = rows
        self.cols = cols
        self.camera_widgets: list[CameraWidget] = []
        self.setup_ui()
        
    def setup_ui(self):
        """Setup user interface"""
        layout = QGridLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Create camera widgets
        slot_index = 0
        for row in range(self.rows):
            for col in range(self.cols):
                cam_widget = CameraWidget(slot_index)
                layout.addWidget(cam_widget, row, col)
                self.camera_widgets.append(cam_widget)
                slot_index += 1
    
    def set_available_sources(self, sources: list):
        """Set available sources for all slots"""
        for widget in self.camera_widgets:
            widget.set_available_sources(sources)
    
    def get_camera_widget(self, slot_index: int) -> CameraWidget:
        """Get camera widget by slot index"""
        if 0 <= slot_index < len(self.camera_widgets):
            return self.camera_widgets[slot_index]
        return None


# Import cv2 at module level
import cv2