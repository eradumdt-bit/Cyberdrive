# 🚗 CyberDrive – v0.1 (Alpha)
CyberDrive is an open-source vehicle communication and visualization platform.
It bridges embedded vehicle electronics with a Windows-based server, serving as a foundation for future autonomous driving systems.

This release represents the first public alpha (v0.1) and focuses on core connectivity and data visualization.

# 🧠 Overview
CyberDrive uses an ESP32 as a communication relay between an Arduino Mega and a Windows server.
This architecture allows real-time vehicle data and camera feeds to be transmitted and displayed on a desktop application.

The project is designed to scale toward autonomous driving, telemetry analysis, and multi-vehicle management.

# 🏗️ Architecture

Arduino Mega: Vehicle logic, sensors, low-level control

ESP32: Communication bridge and network relay

Windows Server: Data visualization, camera feeds, future AI logic

# ✨ Features (v0.1)
🔌 ESP32 bridge between Arduino Mega and Windows

📊 Real-time vehicle data display

📷 Camera feed support

🚘 Multiple vehicle profiles via JSON files

🖥️ Windows-focused desktop/server environment

🧪 Experimental and modular architecture

# 📁 Vehicle Configuration
Vehicles are currently registered using JSON configuration files.

Each vehicle can define:

Identifier / name

Network parameters

Data and feed configuration

⚠️ Manual editing is required in v0.1.

# 🛠️ Planned Features
🧩 Intuitive configuration tool (GUI)

🚗 Simplified vehicle onboarding

🧠 Autonomous driving modules

📡 Improved networking and protocol stability

📊 Advanced telemetry and logging

🔄 Cross-platform support (future)

# 🚧 Project Status
Version: v0.1

Stage: Alpha

Stability: Experimental

Expect bugs, breaking changes, and incomplete features.
APIs and file formats may change without notice.

# 🤝 Contributing
Contributions, ideas, and feedback are welcome!

Fork the project

Create a feature branch

Submit a pull request

Open issues for bugs or suggestions

This project is community-driven and evolving.

# 🧭 Vision
CyberDrive aims to become a modular autonomous vehicle software stack, starting from low-level communication up to perception, control, and intelligence.
