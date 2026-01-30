"""
Camera manager - detects and manages camera sources
"""
import cv2
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import numpy as np
from utils.logger import get_logger
from camera.camera_classifier import CameraClassifier, CameraViewType

logger = get_logger()

@dataclass
class CameraSource:
    """Camera source information"""
    id: str
    name: str
    type: str  # 'usb', 'ip', 'droidcam'
    index: Optional[int] = None  # For USB cameras
    url: Optional[str] = None     # For IP/DroidCam
    resolution: tuple = (640, 480)
    fps: int = 30
    view_type: CameraViewType = field(default=CameraViewType.UNKNOWN)
    view_confidence: float = 0.0
    
class CameraManager:
    """Manage multiple camera sources"""
    
    def __init__(self):
        self._available_sources: List[CameraSource] = []
        self._active_cameras: Dict[str, cv2.VideoCapture] = {}
        self._last_frames: Dict[str, np.ndarray] = {}
        self._classifier = CameraClassifier()
        self._classification_cache: Dict[str, Tuple] = {}  # Cache results
        
    def scan_usb_cameras(self, max_index: int = 10) -> List[CameraSource]:
        """
        Scan for available USB cameras
        
        Args:
            max_index: Maximum camera index to check
            
        Returns:
            List of detected USB camera sources
        """
        sources = []
        
        for i in range(max_index):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)  # DirectShow on Windows
            if cap.isOpened():
                # Get camera name (try to get a meaningful name)
                name = f"USB Camera {i}"
                
                # Test if camera actually works
                ret, frame = cap.read()
                if ret:
                    # Get resolution
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    
                    source = CameraSource(
                        id=f"usb_{i}",
                        name=name,
                        type="usb",
                        index=i,
                        resolution=(width, height)
                    )
                    sources.append(source)
                    logger.info(f"Found USB camera: {name} ({width}x{height})")
                
                cap.release()
        
        return sources
    
    def add_ip_camera(self, name: str, url: str) -> CameraSource:
        """
        Add IP camera source
        
        Args:
            name: Camera name
            url: RTSP/HTTP URL
            
        Returns:
            Camera source
        """
        camera_id = f"ip_{len([s for s in self._available_sources if s.type == 'ip'])}"
        
        source = CameraSource(
            id=camera_id,
            name=name,
            type="ip",
            url=url
        )
        
        self._available_sources.append(source)
        logger.info(f"Added IP camera: {name} ({url})")
        return source
    
    def add_droidcam(self, name: str, ip: str, port: int = 4747) -> CameraSource:
        """
        Add DroidCam source
        
        Args:
            name: Camera name
            ip: Phone IP address
            port: DroidCam port (default 4747)
            
        Returns:
            Camera source
        """
        url = f"http://{ip}:{port}/video"
        camera_id = f"droidcam_{ip.replace('.', '_')}"
        
        source = CameraSource(
            id=camera_id,
            name=name,
            type="droidcam",
            url=url
        )
        
        self._available_sources.append(source)
        logger.info(f"Added DroidCam: {name} ({url})")
        return source
    
    def refresh_sources(self):
        """Refresh available camera sources"""
        self._available_sources.clear()
        
        # Scan USB cameras
        usb_sources = self.scan_usb_cameras()
        self._available_sources.extend(usb_sources)
        
        logger.info(f"Found {len(usb_sources)} USB camera(s)")
    
    def get_available_sources(self) -> List[CameraSource]:
        """Get list of available camera sources"""
        return self._available_sources.copy()
    
    def open_camera(self, source_id: str) -> bool:
        """
        Open camera source
        
        Args:
            source_id: Camera source ID
            
        Returns:
            True if camera opened successfully
        """
        # Find source
        source = None
        for s in self._available_sources:
            if s.id == source_id:
                source = s
                break
        
        if not source:
            logger.error(f"Camera source not found: {source_id}")
            return False
        
        # Close if already open
        if source_id in self._active_cameras:
            self.close_camera(source_id)
        
        # Open camera
        try:
            if source.type == "usb":
                cap = cv2.VideoCapture(source.index, cv2.CAP_DSHOW)
            elif source.type in ["ip", "droidcam"]:
                cap = cv2.VideoCapture(source.url)
            else:
                logger.error(f"Unknown camera type: {source.type}")
                return False
            
            if not cap.isOpened():
                logger.error(f"Failed to open camera: {source.name}")
                return False
            
            # Set properties
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, source.resolution[0])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, source.resolution[1])
            cap.set(cv2.CAP_PROP_FPS, source.fps)
            
            self._active_cameras[source_id] = cap
            logger.info(f"Opened camera: {source.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error opening camera {source.name}: {e}")
            return False
    
    def close_camera(self, source_id: str):
        """Close camera source"""
        if source_id in self._active_cameras:
            self._active_cameras[source_id].release()
            del self._active_cameras[source_id]
            if source_id in self._last_frames:
                del self._last_frames[source_id]
            logger.info(f"Closed camera: {source_id}")
    
    def read_frame(self, source_id: str) -> Optional[np.ndarray]:
        """
        Read frame from camera
        
        Args:
            source_id: Camera source ID
            
        Returns:
            Frame as numpy array (BGR) or None if failed
        """
        if source_id not in self._active_cameras:
            return None
        
        cap = self._active_cameras[source_id]
        ret, frame = cap.read()
        
        if ret:
            self._last_frames[source_id] = frame
            return frame
        else:
            # Return last frame if read failed
            return self._last_frames.get(source_id)
    
    def get_last_frame(self, source_id: str) -> Optional[np.ndarray]:
        """Get last successfully read frame"""
        return self._last_frames.get(source_id)
    
    def is_camera_open(self, source_id: str) -> bool:
        """Check if camera is open"""
        return source_id in self._active_cameras
    
    def close_all(self):
        """Close all cameras"""
        for source_id in list(self._active_cameras.keys()):
            self.close_camera(source_id)