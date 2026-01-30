"""
RC Car Server - Phase 1A
Console test for vehicle connection and basic control
"""
import time
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import setup_logger
from utils.config_loader import ConfigLoader
from vehicle.vehicle_manager import VehicleManager
from core.telemetry import VehicleCommand

def print_banner():
    """Print startup banner"""
    print("\n" + "="*60)
    print("  RC CAR CONTROL SERVER - Phase 1A")
    print("  Console Test Mode")
    print("="*60 + "\n")

def print_menu():
    """Print control menu"""
    print("\n" + "-"*40)
    print("Controls:")
    print("  Z = Forward    S = Backward")
    print("  Q = Left       D = Right")
    print("  Space = Center/Stop")
    print("  X = Exit")
    print("-"*40)

def main():
    """Main entry point"""
    print_banner()
    
    # Setup logger
    logger = setup_logger("RCCarServer", level="INFO", console=True)
    logger.info("Starting RC Car Server...")
    
    # Load server config
    try:
        config = ConfigLoader.load_yaml("config/server_config.yaml")
        logger.info(f"Loaded config: {config['server']['name']} v{config['server']['version']}")
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return
    
    # Initialize vehicle manager
    vehicle_manager = VehicleManager()
    vehicle_manager.load_vehicle_profiles("config/vehicles")
    
    vehicles = vehicle_manager.get_vehicle_list()
    if not vehicles:
        logger.error("No vehicle profiles found!")
        return
    
    # List available vehicles
    print("\nAvailable vehicles:")
    for i, vehicle in enumerate(vehicles, 1):
        print(f"  {i}. {vehicle.name} ({vehicle.id})")
        print(f"     Type: {vehicle.type}")
        print(f"     Connection: {vehicle.connection.preferred_mode}")
    
    # Select vehicle
    print("\nSelect vehicle (1-{}) or 0 to exit: ".format(len(vehicles)), end="")
    try:
        choice = int(input())
        if choice == 0:
            return
        if choice < 1 or choice > len(vehicles):
            logger.error("Invalid choice")
            return
        
        selected_vehicle = vehicles[choice - 1]
    except (ValueError, KeyboardInterrupt):
        print("\nExiting...")
        return
    
    # Connect to vehicle
    logger.info(f"Connecting to {selected_vehicle.name}...")
    if not vehicle_manager.connect_vehicle(selected_vehicle.id):
        logger.error("Failed to connect to vehicle")
        return
    
    conn_info = vehicle_manager.get_connection_info()
    logger.info(f"✓ Connected via {conn_info['type']}")
    
    print_menu()
    print("\n⚠️  Note: Keyboard input mode not fully implemented yet")
    print("Running in test mode - sending neutral commands...\n")
    
    # Main loop - send neutral commands and display telemetry
    try:
        neutral_cmd = VehicleCommand(direction=1500, throttle=1500)
        
        print("Press Ctrl+C to exit\n")
        
        while True:
            # Send neutral command
            vehicle_manager.send_command(neutral_cmd)
            
            # Receive and display telemetry
            telem = vehicle_manager.receive_telemetry()
            if telem:
                print(f"\r[{time.strftime('%H:%M:%S')}] "
                      f"Dir: {telem.direction:4d} | "
                      f"Thr: {telem.throttle:4d} | "
                      f"Dist: {telem.distance_cm:3d}cm | "
                      f"Batt: {telem.battery_voltage:.1f}V | "
                      f"RX: {'✓' if telem.rx_active else '✗'}",
                      end="", flush=True)
            
            time.sleep(0.1)  # 10 Hz update
    
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    
    finally:
        # Cleanup
        logger.info("Disconnecting vehicle...")
        vehicle_manager.disconnect_vehicle(selected_vehicle.id)
        logger.info("Goodbye!")

if __name__ == "__main__":
    main()