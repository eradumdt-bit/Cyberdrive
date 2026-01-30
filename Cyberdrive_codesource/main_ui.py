"""
CyberDrive Control Server - UI Mode
Entry point for graphical interface
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

from ui.main_window import MainWindow
from vehicle.vehicle_manager import VehicleManager
from utils.logger import setup_logger
from utils.config_loader import ConfigLoader

def main():
    """Main entry point"""
    
    # Setup logger
    logger = setup_logger("CyberDrive", level="INFO", console=True)
    logger.info("Starting CyberDrive Control Server (UI Mode)...")
    
    # Load config
    try:
        config = ConfigLoader.load_yaml("config/server_config.yaml")
        logger.info(f"Loaded config: {config['server']['name']} v{config['server']['version']}")
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return 1
    
    # Initialize vehicle manager
    vehicle_manager = VehicleManager()
    vehicle_manager.load_vehicle_profiles("config/vehicles")
    
    vehicles = vehicle_manager.get_vehicle_list()
    if not vehicles:
        logger.warning("No vehicle profiles found!")
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("CyberDrive")
    app.setOrganizationName("CyberDrive")
    
    
    
    # Create and show main window
    window = MainWindow(vehicle_manager)
    window.show()
    
    logger.info("UI ready")
    
    # Run event loop
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())