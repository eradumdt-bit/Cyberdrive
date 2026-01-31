# Changelog

All notable changes to CyberDrive will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.0] - 2025-01-31

### 🎯 Major Features

#### Visual Profile Creator
- **Added** complete visual profile creator dialog (`ui/widgets/profile_creator.py`)
- **Added** zero-code vehicle configuration workflow
- **Added** form-based interface for all vehicle parameters
- **Added** JSON preview before saving
- **Added** automatic validation of all configuration fields
- **Added** helpful tooltips and placeholder text throughout UI

#### Profile Management
- **Added** enhanced vehicle selector with integrated management menu
- **Added** ⚙️ gear icon menu for quick access to profile operations
- **Added** "Create New Profile" menu option
- **Added** "Edit Current Profile" menu option
- **Added** "Delete Current Profile" menu option with confirmation
- **Added** "Refresh List" menu option
- **Added** auto-refresh of vehicle list after profile changes

#### User Experience
- **Added** organized sections for profile configuration:
  - Basic Information (ID, Name, Type, Description)
  - Connection Configuration (Serial, WiFi)
  - Capabilities (Speed, Camera, Sensors, Actuators)
  - Protocol (Version, Command/Telemetry formats)
  - Control Limits (Direction, Throttle PWM values)
- **Added** visual feedback for save/delete operations
- **Added** error messages with specific validation failures
- **Added** smart defaults for common configurations

### 📖 Documentation

- **Added** comprehensive user guide (`PROFILE_CREATOR_README.md`)
- **Added** quick-start guide (`QUICKSTART.txt`)
- **Added** rapid migration guide (`MIGRATION_RAPIDE.py`)
- **Added** technical integration guide (`PROFILE_CREATOR_INTEGRATION_GUIDE.py`)
- **Added** example vehicle profiles:
  - FPV Racing Drone (WiFi-based)
  - Explorer Robot (Serial-based)
- **Added** standalone demo application (`demo_profile_creator.py`)
- **Added** detailed README for v0.2 release

### 🔧 Improvements

- **Improved** vehicle selector architecture with signal-based updates
- **Improved** file management with automatic directory creation
- **Improved** code organization with modular components
- **Improved** error handling throughout profile operations
- **Improved** user feedback with status messages

### 🐛 Bug Fixes

- **Fixed** potential race conditions in vehicle list updates
- **Fixed** file path handling on different Windows configurations
- **Fixed** validation edge cases in PWM limit configuration

### 📦 Internal Changes

- **Refactored** vehicle selector into enhanced version
- **Separated** profile management logic from UI components
- **Added** `profiles_updated` signal for reactive updates
- **Improved** code comments and documentation
- **Added** type hints for better code clarity

---

## [0.1.0] - Initial Release

### Core Features

#### Communication
- **Added** ESP32 bridge implementation
- **Added** Serial communication support
- **Added** WiFi communication support
- **Added** Dual-mode connection (Serial + WiFi)

#### Telemetry
- **Added** Real-time vehicle data reception
- **Added** Telemetry panel with live updates
- **Added** Command transmission to vehicle
- **Added** Heartbeat mechanism for connection stability

#### Camera System
- **Added** Camera feed support
- **Added** Multi-camera grid (2x2)
- **Added** USB camera detection and management
- **Added** Real-time frame updates (30 FPS)
- **Added** Camera source switching

#### Vehicle Management
- **Added** JSON-based vehicle profiles
- **Added** Vehicle selector dropdown
- **Added** Multiple vehicle support
- **Added** Connection info display
- **Added** Vehicle profile loading system

#### User Interface
- **Added** Main window with PyQt6
- **Added** Left panel for controls
- **Added** Right panel for camera feeds
- **Added** Status bar for system messages
- **Added** QSS stylesheet support
- **Added** Dark theme

#### Control
- **Added** Keyboard control support (ZQSD + Space)
- **Added** Direction and throttle control
- **Added** Manual/automatic mode switching
- **Added** Neutral position on key release

### Configuration
- **Added** YAML-based server configuration
- **Added** JSON vehicle profile format
- **Added** Example vehicle profile (RC Car)
- **Added** Config directory structure

### Architecture
- **Added** Modular package structure
- **Added** Adapter pattern for connections
- **Added** Manager classes for components
- **Added** Logging system
- **Added** Signal/slot architecture

### Documentation
- **Added** Initial README
- **Added** Requirements file
- **Added** Build script for executable
- **Added** Project structure

---

## Types of Changes

- `Added` for new features
- `Changed` for changes in existing functionality
- `Deprecated` for soon-to-be removed features
- `Removed` for now removed features
- `Fixed` for any bug fixes
- `Security` in case of vulnerabilities

---

## Version History

- **v0.2.0** - Visual Profile Creator (Current)
- **v0.1.0** - Initial Release

---

## Upcoming (v0.3.0 - Planned)

### Features in Development
- Enhanced camera controls (exposure, focus, resolution)
- Telemetry recording and playback
- Graph-based telemetry visualization
- Improved connection reliability
- Better error recovery mechanisms
- Export/import vehicle profiles
- Profile templates library

### Under Consideration
- Web-based dashboard
- Multi-language support
- Plugin architecture
- Advanced logging system
- Performance monitoring
- Network diagnostics tools

---

## Migration Guides

### From v0.1 to v0.2

**No breaking changes!** v0.2 is fully backward compatible.

**Optional upgrades:**
1. Replace `vehicle_selector.py` with `vehicle_selector_enhanced.py`
2. Add one line in `setup_connections()`:
   ```python
   self.vehicle_selector.profiles_updated.connect(self.load_vehicles)
   ```
3. Enjoy the new profile creator!

**Existing JSON profiles** continue to work without modification.

---

## Known Issues

### v0.2.0
- Windows-only support (Linux/macOS in development)
- Camera detection may fail on some USB configurations
- Serial port auto-detection limited on some systems
- Large telemetry data may cause UI lag

### Workarounds
- Use manual port specification if AUTO fails
- Restart application if camera doesn't appear
- Reduce telemetry update rate if experiencing lag

---

## Contributing

See CONTRIBUTING.md for guidelines on submitting changes.

All contributions are tracked in this changelog.

---

**Last Updated**: 2025-01-31
