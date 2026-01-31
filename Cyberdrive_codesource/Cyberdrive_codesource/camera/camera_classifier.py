"""
Camera classifier - Auto-detect camera view type
Uses simple heuristics for now (can be upgraded to ML later)
"""
import cv2
import numpy as np
from typing import Optional, Tuple
from enum import Enum

class CameraViewType(Enum):
    """Types of camera views"""
    FRONT = "front"           # Vue avant voiture (route devant)
    REAR = "rear"             # Vue arrière
    LEFT = "left"             # Vue latérale gauche
    RIGHT = "right"           # Vue latérale droite
    OVERHEAD = "overhead"     # Vue de dessus / externe
    INTERIOR = "interior"     # Vue intérieur / cockpit
    UNKNOWN = "unknown"       # Type inconnu

class CameraClassifier:
    """Classify camera view type from frames"""
    
    def __init__(self):
        self.view_icons = {
            CameraViewType.FRONT: "🚗→",
            CameraViewType.REAR: "←🚗",
            CameraViewType.LEFT: "↖🚗",
            CameraViewType.RIGHT: "🚗↗",
            CameraViewType.OVERHEAD: "🛰️",
            CameraViewType.INTERIOR: "👤",
            CameraViewType.UNKNOWN: "📷"
        }
    
    def classify_from_frames(self, frames: list) -> Tuple[CameraViewType, float]:
        """
        Classify camera view from multiple frames
        
        Args:
            frames: List of frames (numpy arrays)
            
        Returns:
            (view_type, confidence) tuple
        """
        if not frames:
            return (CameraViewType.UNKNOWN, 0.0)
        
        # Take middle frame for analysis
        frame = frames[len(frames) // 2]
        
        # Analyze frame
        return self._analyze_frame(frame)
    
    def _analyze_frame(self, frame: np.ndarray) -> Tuple[CameraViewType, float]:
        """
        Analyze single frame to determine view type
        Uses heuristics based on image characteristics
        """
        if frame is None or frame.size == 0:
            return (CameraViewType.UNKNOWN, 0.0)
        
        h, w = frame.shape[:2]
        
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Analyze different regions
        top_third = gray[0:h//3, :]
        middle_third = gray[h//3:2*h//3, :]
        bottom_third = gray[2*h//3:h, :]
        
        # Calculate brightness for each region
        top_brightness = np.mean(top_third)
        middle_brightness = np.mean(middle_third)
        bottom_brightness = np.mean(bottom_third)
        
        # Calculate edges (road detection)
        edges = cv2.Canny(gray, 50, 150)
        bottom_edges = edges[2*h//3:h, :]
        edge_density = np.sum(bottom_edges > 0) / bottom_edges.size
        
        # Heuristic rules
        confidence = 0.5
        
        # FRONT VIEW: Sky (bright) at top, road (edges) at bottom
        if top_brightness > middle_brightness and edge_density > 0.05:
            return (CameraViewType.FRONT, 0.7)
        
        # OVERHEAD: Uniform brightness, less edges
        if abs(top_brightness - bottom_brightness) < 20 and edge_density < 0.03:
            return (CameraViewType.OVERHEAD, 0.6)
        
        # REAR VIEW: Similar to front but often darker at top
        if bottom_brightness > top_brightness and edge_density > 0.04:
            return (CameraViewType.REAR, 0.6)
        
        # INTERIOR: Often darker, less structure
        if np.mean(gray) < 80:
            return (CameraViewType.INTERIOR, 0.5)
        
        return (CameraViewType.UNKNOWN, 0.3)
    
    def get_icon(self, view_type: CameraViewType) -> str:
        """Get emoji icon for view type"""
        return self.view_icons.get(view_type, "📷")
    
    def get_description(self, view_type: CameraViewType) -> str:
        """Get human-readable description"""
        descriptions = {
            CameraViewType.FRONT: "Front View (Forward)",
            CameraViewType.REAR: "Rear View (Backward)",
            CameraViewType.LEFT: "Left Side View",
            CameraViewType.RIGHT: "Right Side View",
            CameraViewType.OVERHEAD: "Overhead / External",
            CameraViewType.INTERIOR: "Interior / Cockpit",
            CameraViewType.UNKNOWN: "Unknown View"
        }
        return descriptions.get(view_type, "Unknown")