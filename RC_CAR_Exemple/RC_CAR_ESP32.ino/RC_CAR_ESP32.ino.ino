/*
  ESP32 - Bridge Final PC ↔ Arduino
  
  Connexions:
  - USB → PC (Serial, 115200 baud)
  - TX2 (GPIO17) → RX1 Arduino (Pin 19)
  - RX2 (GPIO16) ← TX1 Arduino (Pin 18)
  - GND ↔ Arduino GND
  
  Protocol:
  PC → ESP32: CMD:MOVE:1500:1500\n
  ESP32 → Arduino: CMD:1500:1500\n
  Arduino → ESP32: TELEM:1500:1500:45:11.4:1\n
  ESP32 → PC: TELEM:1500:1500:45:11.4:1\n
*/

#define SERIAL_PC Serial        // USB vers PC
#define SERIAL_ARDUINO Serial2  // UART2 vers Arduino

const int RX_PIN = 16;  // GPIO16 = RX2
const int TX_PIN = 17;  // GPIO17 = TX2

String pcBuffer = "";
String arduinoBuffer = "";

unsigned long lastPCCommand = 0;
unsigned long lastArduinoTelem = 0;
unsigned long statsTimer = 0;

uint32_t cmdCount = 0;
uint32_t telemCount = 0;

void setup() {
  // Serial USB vers PC
  SERIAL_PC.begin(115200);
  delay(500);
  
  // Serial vers Arduino
  SERIAL_ARDUINO.begin(115200, SERIAL_8N1, RX_PIN, TX_PIN);
  delay(100);
  
  SERIAL_PC.println();
  SERIAL_PC.println("ESP32 Bridge Ready");
  SERIAL_PC.println("PC <-> Arduino");
}

void loop() {
  // ========== PC → ESP32 → Arduino ==========
  while (SERIAL_PC.available()) {
    char c = SERIAL_PC.read();
    
    if (c == '\n') {
      if (pcBuffer.length() > 0) {
        handlePCCommand(pcBuffer);
        pcBuffer = "";
      }
    } else if (c != '\r') {
      pcBuffer += c;
    }
  }
  
  // ========== Arduino → ESP32 → PC ==========
  while (SERIAL_ARDUINO.available()) {
    char c = SERIAL_ARDUINO.read();
    
    if (c == '\n') {
      if (arduinoBuffer.length() > 0) {
        handleArduinoData(arduinoBuffer);
        arduinoBuffer = "";
      }
    } else if (c != '\r') {
      arduinoBuffer += c;
    }
  }
  
  // Stats debug (optionnel)
  if (millis() - statsTimer > 10000) {
    statsTimer = millis();
    // SERIAL_PC.print("ESP32 Stats - CMD:");
    // SERIAL_PC.print(cmdCount);
    // SERIAL_PC.print(" TELEM:");
    // SERIAL_PC.println(telemCount);
  }
  
  delay(1);
}

void handlePCCommand(String data) {
  data.trim();
  
  // Heartbeat (nouveau)
  if (data == "PING") {
    SERIAL_PC.println("PONG");
    // Forward aussi à l'Arduino pour qu'il sache que le serveur est connecté
    SERIAL_ARDUINO.println("PING");
    return;
  }
  
  // Format: CMD:MOVE:{dir}:{thr}
  if (data.startsWith("CMD:MOVE:")) {
    int firstColon = data.indexOf(':', 9);
    int secondColon = data.indexOf(':', firstColon + 1);
    
    if (firstColon > 0 && secondColon > 0) {
      String dirStr = data.substring(9, firstColon);
      String thrStr = data.substring(firstColon + 1, secondColon);
      
      int dir = dirStr.toInt();
      int thr = thrStr.toInt();
      
      if (dir >= 1000 && dir <= 2000 && thr >= 1000 && thr <= 2000) {
        // Forward to Arduino
        SERIAL_ARDUINO.print("CMD:");
        SERIAL_ARDUINO.print(dir);
        SERIAL_ARDUINO.print(":");
        SERIAL_ARDUINO.println(thr);
        
        cmdCount++;
        lastPCCommand = millis();
      }
    }
  }
}

void handleArduinoData(String data) {
  data.trim();
  
  // Forward all TELEM directly to PC
  if (data.startsWith("TELEM:")) {
    SERIAL_PC.println(data);
    telemCount++;
    lastArduinoTelem = millis();
  }
  // Ignore other messages or log them
}