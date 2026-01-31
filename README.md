# 🚗 CyberDrive – v0.2 (Alpha)

**An open-source vehicle communication and visualization platform with zero-code configuration.**

CyberDrive bridges embedded vehicle electronics with a Windows-based server, serving as a foundation for future autonomous driving systems. Version 0.2 introduces **visual profile creation** — no more manual JSON editing required.

---

## 🧠 Overview

CyberDrive uses an ESP32 as a communication relay between an Arduino Mega and a Windows server. This architecture enables real-time vehicle data and camera feeds to be transmitted and displayed on a desktop application. The project is designed to scale toward autonomous driving, telemetry analysis, and multi-vehicle management.

---

## 🏗️ Architecture

```
Arduino Mega    →    ESP32 Bridge    →    Windows Server
 (Vehicle Logic)    (Network Relay)      (Visualization & AI)
```

- **Arduino Mega**: Vehicle logic, sensors, low-level control
- **ESP32**: Communication bridge and network relay
- **Windows Server**: Data visualization, camera feeds, future AI logic

---

## ✨ What's New in v0.2

### 🎯 **Zero-Code Vehicle Configuration**

The biggest addition in v0.2 is the **built-in Profile Creator** — a visual interface that lets you create, edit, and manage vehicle profiles without touching a single line of JSON.

**Features:**
- ✅ **Create profiles** with an intuitive graphical interface
- ✅ **Edit existing profiles** with a single click
- ✅ **Delete obsolete profiles** from the UI
- ✅ **Preview JSON** before saving
- ✅ **Automatic validation** of all fields
- ✅ **Live refresh** of vehicle list after changes

**No more manual JSON editing!** 🎉

---

## 🚀 Features (v0.2)

### Core Features
- 🔌 **ESP32 bridge** between Arduino Mega and Windows
- 📊 **Real-time vehicle data** display
- 📷 **Camera feed support** with multi-camera grid
- 🚘 **Multiple vehicle profiles** via JSON configuration
- 🖥️ **Windows-focused** desktop/server environment

### New in v0.2
- 🎨 **Visual Profile Creator** — create vehicles with clicks, not code
- ⚙️ **Profile Management Menu** — create/edit/delete directly from UI
- 🔄 **Auto-refresh** vehicle list after profile changes
- 👁️ **JSON Preview** before saving
- ✅ **Built-in validation** prevents invalid configurations
- 📝 **Form-based editing** for all vehicle parameters

---

## 📁 Vehicle Configuration

### The Old Way (v0.1)
```json
{
  "id": "rc_car_001",
  "name": "RC Car Proto v1",
  "type": "rc_car",
  "connection": { ... },
  "capabilities": { ... }
}
```
Manual JSON editing required ❌

### The New Way (v0.2)
1. Click the **⚙️** button in the vehicle selector
2. Select **"Create New Profile"**
3. Fill in the form with your vehicle specs
4. Click **"Save Profile"**
5. Done! ✅

**No code required!**

---

## 🎯 Creating Your First Vehicle Profile

### Step 1: Open Profile Creator
Click the **⚙️ gear icon** next to the vehicle selector, then select **"➕ Create New Profile"**.

### Step 2: Fill in Basic Information
- **Vehicle ID**: `my_rc_car` (unique identifier)
- **Name**: `My RC Car` (display name)
- **Type**: `rc_car` (or drone, robot, etc.)
- **Description**: Brief description of your vehicle

### Step 3: Configure Connection
- **Mode**: Serial, WiFi, or Both
- **Serial**: Port (`AUTO` or `COM3`), Baudrate (`115200`)
- **WiFi**: IP address and port

### Step 4: Set Capabilities
- **Max Speed**: Maximum speed in km/h
- **Camera**: Check if onboard camera available
- **Sensors**: List sensors (one per line)
- **Actuators**: List actuators (one per line)

### Step 5: Define Protocol
- **Version**: Protocol version (e.g., `esp32_v1`)
- **Command Format**: `CMD:MOVE:{dir}:{thr}\n`
- **Telemetry Format**: Expected response format

### Step 6: Configure Control Limits
- **Direction**: Min/Center/Max PWM values (typically 1000/1500/2000)
- **Throttle**: Min/Neutral/Max PWM values

### Step 7: Save
Click **"💾 Save Profile"** — your vehicle is now ready to use!

---

## 🛠️ Profile Management

### Create a New Profile
**⚙️ Menu → ➕ Create New Profile**

Opens a guided form with all configuration fields organized by category.

### Edit an Existing Profile
**⚙️ Menu → ✏️ Edit Current Profile**

Loads the selected vehicle's configuration for editing. Modify any field and save.

### Delete a Profile
**⚙️ Menu → 🗑️ Delete Current Profile**

Removes the selected profile after confirmation.

### Refresh Vehicle List
**⚙️ Menu → 🔄 Refresh List**

Manually reload the vehicle list (automatic in most cases).

---

## 📋 Profile Configuration Fields

### Basic Information
- Vehicle ID (unique)
- Display name
- Vehicle type (rc_car, drone, robot, custom)
- Description

### Connection
- **Preferred Mode**: serial / wifi / both
- **Serial**: Port, baudrate, description
- **WiFi**: IP address, port, enabled status

### Capabilities
- Max speed (km/h)
- Onboard camera (yes/no)
- Sensors list
- Actuators list

### Protocol
- Version string
- Command format (with `{dir}` and `{thr}` placeholders)
- Telemetry format

### Control Limits
- **Direction**: Min, center, max PWM values
- **Throttle**: Min, neutral, max PWM values

All fields include tooltips and examples to guide you!

---

## 🎨 User Interface Improvements

### Vehicle Selector Enhancement
The vehicle selector now includes a **⚙️ management menu** with quick access to:
- Create new profiles
- Edit current profile
- Delete profiles
- Refresh list

### Profile Creator Dialog
A clean, organized interface with:
- **Tabbed sections** for easy navigation
- **Real-time validation** with helpful error messages
- **JSON preview** to verify configuration
- **Smart defaults** for common settings
- **Tooltips and hints** throughout

---

## 🚧 Project Status

- **Version**: v0.2
- **Stage**: Alpha
- **Stability**: Experimental

**What's working:**
- ✅ Vehicle communication (Serial/WiFi)
- ✅ Real-time telemetry display
- ✅ Camera feed visualization
- ✅ Visual profile creation and editing
- ✅ Multi-vehicle support

**Known limitations:**
- Windows-focused (Linux/macOS support planned)
- Manual ESP32/Arduino firmware setup required
- Limited documentation for firmware

Expect bugs, breaking changes, and incomplete features. APIs and file formats may change without notice.

---


## 🗺️ Roadmap

### ✅ Completed (v0.2)
- Visual vehicle profile creator
- Profile management UI
- JSON preview and validation
- Auto-refresh on profile changes

### 🚧 In Progress (v0.3)
- Enhanced camera controls
- Telemetry recording and playback
- Improved serial/WiFi connection handling
- Better error messages and logging

### 🔮 Planned (v0.4+)
- **Autonomous driving modules**
- **AI integration** (computer vision, path planning)
- **Cross-platform support** (Linux, macOS)
- **Web dashboard** for remote monitoring
- **Multi-vehicle coordination**
- **Advanced telemetry analysis**
- **Plugin system** for extensibility

---

## 🧩 Example Vehicle Profiles

Two example profiles are included in `config/vehicles/`:

### FPV Racing Drone
```
Type: Drone
Connection: WiFi (192.168.4.1)
Sensors: GPS, IMU, Barometer, Battery
Actuators: 4x ESC, Camera Gimbal, LED
Max Speed: 80 km/h
```

### Explorer Robot
```
Type: Robot
Connection: Serial (AUTO, 115200)
Sensors: Ultrasonic (4x), LIDAR, IMU, Encoders
Actuators: DC Motors (2x), Gripper, Camera Servos
Max Speed: 5 km/h
```

These can be loaded, edited, and customized using the profile creator.

---

## 🤝 Contributing

Contributions, ideas, and feedback are welcome!

1. **Fork** the project
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m 'Add amazing feature'`
4. **Push** to the branch: `git push origin feature/amazing-feature`
5. **Open** a pull request

### Ways to Contribute
- 🐛 Report bugs and issues
- 💡 Suggest new features
- 📖 Improve documentation
- 🧪 Add test cases
- 🎨 Enhance UI/UX
- 🔧 Fix bugs and improve code

This project is **community-driven** and evolving.

---

## 📄 License

This project is open-source. Check the LICENSE file for details.

---

## 🧭 Vision

CyberDrive aims to become a **modular autonomous vehicle software stack**, starting from low-level communication up to perception, control, and intelligence.

Our goal is to make autonomous vehicle development accessible, modular, and collaborative — empowering hobbyists, researchers, and developers to build the future of transportation.

**From RC cars to real vehicles. From telemetry to autonomy.**

---

## 📞 Support & Community

- **GitHub Issues**: For bug reports and feature requests
- **Discussions**: For questions and community chat
- **Documentation**: See `/docs` folder for detailed guides

---

## 🎉 Changelog

### v0.2 (Current)
- ➕ **NEW**: Visual profile creator with zero-code configuration
- ➕ **NEW**: Profile management menu (create/edit/delete)
- ➕ **NEW**: JSON preview and validation
- ➕ **NEW**: Auto-refresh on profile changes
- ➕ **NEW**: Example profiles (drone, robot)
- 🔧 **IMPROVED**: Vehicle selector with integrated management
- 🔧 **IMPROVED**: User experience and interface polish
- 📖 **DOCS**: Comprehensive documentation added

### v0.1 (Initial Release)
- Initial ESP32 bridge implementation
- Real-time vehicle data display
- Camera feed support
- Manual JSON-based vehicle configuration
- Windows server application
- Basic telemetry visualization

---

## 🙏 Acknowledgments

Thanks to all contributors, testers, and community members who help make CyberDrive better!

Special thanks to the open-source community for the amazing tools and libraries that make this project possible.

---

**Built with ❤️ by the CyberDrive community**

*Empowering the next generation of autonomous vehicles*
