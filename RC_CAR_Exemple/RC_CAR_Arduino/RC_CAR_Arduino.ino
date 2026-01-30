/*
  RC Car - Full integrated (Mega 2560) - final with ESP32 integration
  - Receiver dir IN on D2 (interrupt)
  - Receiver thr IN on D3 (interrupt)
  - Servo out D9
  - ESC out D10
  - Power sense A0 (after LiPo switch)
  - HC-SR04 TRIG D6, ECHO D7
  - Activity LED D13
  - LCD I2C 0x3E (16x4)
  - OLED SSD1306 I2C 0x3C
  - MPU-6500 I2C @0x68
  - Button LCD D5 (short press cycles LCD pages, long press skip power/wait)
  - Button OLED D14 (cycles OLED pages only)
  - Long-press on D5: skip waiting power or skip waiting RX (enter debug mode)
*/

#include <Servo.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <math.h>

// ---------- CONFIG ----------
const bool STRICT_RX_REQUIRE_DIR = true;
const unsigned long RX_TIMEOUT_MS = 500;      // ms
const unsigned int INTERVAL_MIN_MS = 8;
const unsigned int INTERVAL_MAX_MS = 60;
const unsigned int VALID_MIN_US = 900;
const unsigned int VALID_MAX_US = 2100;
const unsigned long BASELINE_CAPTURE_MS = 1000;
const unsigned long MOVEMENT_HOLD_MS = 400;
const unsigned int MOVEMENT_DELTA_US = 10;
const unsigned long SERIAL_PRINT_INTERVAL = 200;
const unsigned long PING_INTERVAL = 120;
const int OBSTACLE_CM = 20;
const int CLEAR_CM = 25;
const int N_CLOSE = 2;
const int N_CLEAR = 2;
// sweep interval set to 15s (was 3s)
const unsigned long NO_RX_SWEEP_INTERVAL = 15000;
const unsigned long BOOT_MIN_LEFT_MS = 500;
const unsigned long BOOT_MIN_RIGHT_MS = 700;
const unsigned long BOOT_CENTER_MS = 400;

// debug mode flag (set when user long-press skip RX waiting)
bool debugMode = false;

// Power thresholds
const int POWER_HIGH_THR = 600;
const int POWER_LOW_THR  = 400;
const int POWER_DEBOUNCE_COUNT = 4;
const unsigned long POWER_SAMPLE_MS = 80;

// PWM anomalies detection for RC battery low
const unsigned long RC_NOISE_WINDOW_MS = 2000;
const int RC_NOISE_THRESHOLD = 10;

// ---------- PINS ----------
const uint8_t PIN_DIR_IN    = 2;
const uint8_t PIN_THR_IN    = 3;
const uint8_t PIN_SERVO_OUT = 9;
const uint8_t PIN_ESC_OUT   = 10;
const uint8_t PIN_POWER_A0  = A0;
const uint8_t PIN_TRIG      = 6;
const uint8_t PIN_ECHO      = 7;
const uint8_t PIN_LED       = 13;
const uint8_t PIN_BTN_LCD   = 5;   // controls LCD only
const uint8_t PIN_PWM_LED   = 11;
const uint8_t PIN_TURN_L    = 12;
const uint8_t PIN_TURN_R    = 8;
const uint8_t PIN_BRAKE     = 4;
const uint8_t PIN_BTN_OLED  = 14;  // controls OLED only (D14 on Mega, A0 on Uno)

// ---------- HARDWARE ----------
Servo servoOut;
Servo escOut;
LiquidCrystal_I2C lcd(0x3E, 16, 4);
bool lcdPresent = false;

// OLED configuration (Adafruit)
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET    -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// ---------- MPU ----------
#define MPU_ADDR 0x68
int16_t accX=0, accY=0, accZ=0;
int16_t gyroX=0, gyroY=0, gyroZ=0;
int16_t tempRaw=0;

// ---------- Volatile PWM (ISR) ----------
volatile unsigned long dirRiseUs = 0;
volatile unsigned long dirLastMicros = 0;
volatile unsigned long dirPrevMicros = 0;
volatile unsigned int  dirPulseUs = 1500;

volatile unsigned long thrRiseUs = 0;
volatile unsigned long thrLastMicros = 0;
volatile unsigned long thrPrevMicros = 0;
volatile unsigned int  thrPulseUs = 1500;

// ---------- State ----------
unsigned int dirLastPublished = 1500;
unsigned int thrLastPublished = 1500;
unsigned long lastMovementMs = 0;
unsigned long lastSerialPrint = 0;

unsigned int baseDir = 1500;
unsigned int baseThr = 1500;
bool haveBaseDir = false;
bool haveBaseThr = false;

bool rxSerialOverride = false;
unsigned long rxSerialOverrideTs = 0;
const unsigned long RX_OVERRIDE_TIMEOUT_MS = 2000;

bool awaitingRX = true;
bool carPowered = false;
bool booting = false;
unsigned long bootStartMs = 0;

bool danceMode = false;
unsigned long danceStartMs = 0;

bool testMode = false;
unsigned long testStartMs = 0;

unsigned long lastPingMs = 0;
int distanceCm = -1;
int closeCount = 0;
int clearCount = 0;
bool obstacleStop = false;

unsigned long lastNoRxSweepMs = 0;
bool sweepActive = false;
unsigned long sweepStartMs = 0;
int sweepPhase = 0;

int lcdPage = 0;
int oledPage = 0;

// ===== AJOUT: État serveur =====
bool serverConnected = false;
unsigned long lastServerCommandMs = 0;
const unsigned long SERVER_TIMEOUT_MS = 2000;
int serverDir = 1500;
int serverThr = 1500;
bool serverMode = false;
String esp32Buffer = "";

// power sampling
unsigned long lastPowerSampleMs = 0;
int powerHighCount = 0;
int powerLowCount = 0;

// popup
bool popupShown = false;
unsigned long popupStart = 0;
const unsigned long POPUP_TIME_MS = 2500;
String popupMsg = "";

// RC low battery detection (noise counting)
unsigned long rcNoiseWindowStart = 0;
int rcNoiseCount = 0;
bool rcBatteryLow = false;

// turn signals
unsigned long lastTurnBlink = 0;
const unsigned long TURN_BLINK_MS = 400;
bool turnState = false;

// button state trackers and long press for LCD button
bool btnLCDPrev = HIGH;
bool btnOLEDPrev = HIGH;
unsigned long btnLCDPressedTs = 0;
bool btnLCDLongHandled = false;
const unsigned long LONG_PRESS_MS = 2000;

// ---------- PROTOTYPES ----------
void dirISR();
void thrISR();
unsigned int copyDirPulse();
unsigned int copyThrPulse();
unsigned long copyDirLastMicros();
unsigned long copyDirPrevMicros();
unsigned long copyThrLastMicros();
unsigned long copyThrPrevMicros();
bool channelFresh(unsigned long lastMicros, unsigned long prevMicros, unsigned long nowMs);
void lcdPrintLine(int row, const String &s);
int pingOnce();
int pingMedian3();
void startBoot(unsigned long nowMs);
void processBoot(unsigned long nowMs);
void checkNoRxSweep(unsigned long nowMs);
void handleButtons();               // will call both handlers
void handleButtonLCD();             // LCD button logic (D5)
void handleButtonOLED();            // OLED button logic (D14)
int mapThrottleToPWM(unsigned int thrUs);
void captureBaselineOnce();
void runTestSequenceNonBlocking(unsigned long nowMs);
void readMPU();
void oled_page_face(uint8_t frame);
void oled_page_mpu();
void oled_page_system();

// ---------- ISR implementations ----------
void dirISR() {
  bool lvl = digitalRead(PIN_DIR_IN);
  unsigned long now = micros();
  if (lvl) {
    dirRiseUs = now;
  } else {
    if (dirRiseUs != 0) {
      unsigned long dur = now - dirRiseUs;
      if (dur >= VALID_MIN_US && dur <= VALID_MAX_US) {
        dirPulseUs = (unsigned int)dur;
        dirPrevMicros = dirLastMicros;
        dirLastMicros = now;
      }
    }
  }
}

void thrISR() {
  bool lvl = digitalRead(PIN_THR_IN);
  unsigned long now = micros();
  if (lvl) {
    thrRiseUs = now;
  } else {
    if (thrRiseUs != 0) {
      unsigned long dur = now - thrRiseUs;
      if (dur >= VALID_MIN_US && dur <= VALID_MAX_US) {
        thrPulseUs = (unsigned int)dur;
        thrPrevMicros = thrLastMicros;
        thrLastMicros = now;
      }
    }
  }
}

// ---------- safe copies ----------
unsigned int copyDirPulse()   { noInterrupts(); unsigned int v = dirPulseUs; interrupts(); return v; }
unsigned int copyThrPulse()   { noInterrupts(); unsigned int v = thrPulseUs; interrupts(); return v; }
unsigned long copyDirLastMicros() { noInterrupts(); unsigned long v = dirLastMicros; interrupts(); return v; }
unsigned long copyDirPrevMicros() { noInterrupts(); unsigned long v = dirPrevMicros; interrupts(); return v; }
unsigned long copyThrLastMicros() { noInterrupts(); unsigned long v = thrLastMicros; interrupts(); return v; }
unsigned long copyThrPrevMicros() { noInterrupts(); unsigned long v = thrPrevMicros; interrupts(); return v; }

// ---------- helpers ----------
bool channelFresh(unsigned long lastMicros, unsigned long prevMicros, unsigned long nowMs) {
  if (lastMicros == 0 || prevMicros == 0) return false; // need two falling edges
  unsigned long ageMs = (nowMs * 1000UL > lastMicros) ? ((nowMs * 1000UL - lastMicros)/1000UL) : 0;
  if (ageMs > RX_TIMEOUT_MS) return false;
  unsigned long intervalMs = (lastMicros > prevMicros) ? ((lastMicros - prevMicros)/1000UL) : 0;
  if (intervalMs < INTERVAL_MIN_MS || intervalMs > INTERVAL_MAX_MS) return false;
  return true;
}

void lcdPrintLine(int row, const String &s) {
  static String last[4] = {"","","",""};
  if (!lcdPresent) return;
  if (row < 0 || row > 3) return;
  if (last[row] != s) {
    lcd.setCursor(0, row);
    lcd.print(s);
    for (int i = s.length(); i < 16; ++i) lcd.print(' ');
    last[row] = s;
  }
}

// ---------- HC-SR04 ----------
int pingOnce() {
  digitalWrite(PIN_TRIG, LOW); delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH); delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);
  unsigned long dur = pulseIn(PIN_ECHO, HIGH, 25000);
  if (dur == 0) return -1;
  return (int)(dur * 0.034 / 2.0 + 0.5);
}
int pingMedian3() {
  int a = pingOnce(); delay(6);
  int b = pingOnce(); delay(6);
  int c = pingOnce();
  if (a<0 && b<0 && c<0) return -1;
  int aa = (a<0)?10000:a;
  int bb = (b<0)?10000:b;
  int cc = (c<0)?10000:c;
  int med;
  if ((aa <= bb && bb <= cc) || (cc <= bb && bb <= aa)) med = bb;
  else if ((bb <= aa && aa <= cc) || (cc <= aa && aa <= bb)) med = aa;
  else med = cc;
  if (med == 10000) return -1;
  return med;
}

// ---------- Boot ----------
void startBoot(unsigned long nowMs) {
  booting = true;
  bootStartMs = nowMs;
  // start left immediately for visible effect (servo will be forced mid if awaitingRX/debugMode)
  servoOut.writeMicroseconds(1000);
  digitalWrite(PIN_LED, HIGH);
}

void processBoot(unsigned long nowMs) {
  unsigned long t = nowMs - bootStartMs;
  const unsigned long totalBootTime = BOOT_MIN_LEFT_MS + BOOT_MIN_RIGHT_MS + BOOT_CENTER_MS;
  int BARLEN = 16;
  int progress = (t >= totalBootTime) ? BARLEN : (int)((uint32_t)t * BARLEN / totalBootTime);
  String bar = "BOOT:[";
  for (int i=0;i<progress;i++) bar += '#';
  for (int i=progress;i<BARLEN;i++) bar += '-';
  bar += "]";
  lcdPrintLine(0, bar.substring(0,16));

  if (t < BOOT_MIN_LEFT_MS) {
    servoOut.writeMicroseconds(1000);
  } else if (t < (BOOT_MIN_LEFT_MS + BOOT_MIN_RIGHT_MS)) {
    servoOut.writeMicroseconds(2000);
  } else if (t < (BOOT_MIN_LEFT_MS + BOOT_MIN_RIGHT_MS + BOOT_CENTER_MS)) {
    servoOut.writeMicroseconds(1500);
  }

  static unsigned long blinkTs = 0;
  static bool st = false;
  if (millis() - blinkTs > 160) { blinkTs = millis(); st = !st; digitalWrite(PIN_LED, st?HIGH:LOW); }

  if (t >= (BOOT_MIN_LEFT_MS + BOOT_MIN_RIGHT_MS + BOOT_CENTER_MS)) {
    booting = false;
    awaitingRX = true;
    lcdPrintLine(0, "Waiting RX...");
    lcdPrintLine(1, "                ");
    lcdPrintLine(2, "                ");
    lcdPrintLine(3, "                ");
    // center servo to be safe
    servoOut.writeMicroseconds(1500);
    digitalWrite(PIN_LED, LOW);
  }
}

// ---------- no-RX sweep ----------
void checkNoRxSweep(unsigned long nowMs) {
  // Only set sweepActive periodically; movement itself won't drive outputs when awaitingRX/debugMode
  if (awaitingRX && !danceMode && !testMode) {
    if (nowMs - lastNoRxSweepMs >= NO_RX_SWEEP_INTERVAL) {
      lastNoRxSweepMs = nowMs;
      sweepActive = true;
      sweepStartMs = nowMs;
      sweepPhase = 1;
    }
  }

  if (sweepActive) {
    unsigned long t = nowMs - sweepStartMs;
    if (sweepPhase == 1 && t > 600) { /* would move servo to right */ sweepPhase = 2; }
    else if (sweepPhase == 2 && t > 1200) { /* center */ sweepPhase = 3; }
    else if (sweepPhase == 3 && t > 1500) { sweepActive = false; sweepPhase = 0; }
  }
}

// ---------- Button handling (LCD + OLED separated) ----------
void handleButtons() {
  handleButtonLCD();
  handleButtonOLED();
}

// LCD Button (PIN_BTN_LCD): short press cycles LCD pages; long press = skip power / skip RX -> debug
void handleButtonLCD() {
  bool state = digitalRead(PIN_BTN_LCD);
  unsigned long now = millis();

  // detect edge: pressed = LOW (INPUT_PULLUP)
  if (btnLCDPrev == HIGH && state == LOW) {
    // pressed now
    btnLCDPressedTs = now;
    btnLCDLongHandled = false;
  } else if (btnLCDPrev == LOW && state == LOW) {
    // still pressed -> long press check
    if (!btnLCDLongHandled && (now - btnLCDPressedTs >= LONG_PRESS_MS)) {
      btnLCDLongHandled = true;
      // long-press action:
      if (!carPowered) {
        // skip waiting power
        carPowered = true;
        lcdPrintLine(0, "Power OVERRIDE");
        lcdPrintLine(1, "User forced ON");
        popupMsg = "POWER SKIPPED";
        popupShown = true; popupStart = now;
        captureBaselineOnce();
        startBoot(now);
      } else if (awaitingRX && !debugMode) {
        // skip waiting RX -> enter debug mode (locks outputs to 1500)
        rxSerialOverride = true;
        rxSerialOverrideTs = now;
        awaitingRX = false;
        debugMode = true;
        popupMsg = "RX SKIPPED - DEBUG";
        popupShown = true; popupStart = now;
      } else if (debugMode) {
        // long press again to exit debug mode
        debugMode = false;
        rxSerialOverride = false;
        popupMsg = "DEBUG OFF";
        popupShown = true; popupStart = now;
      }
    }
  } else if (btnLCDPrev == LOW && state == HIGH) {
    // released: if it was a short press (not long handled) -> cycle LCD pages
    if (!btnLCDLongHandled) {
      lcdPage = (lcdPage + 1) % 3;
    }
    btnLCDLongHandled = false;
  }

  btnLCDPrev = state;
}

// OLED Button (PIN_BTN_OLED): short press cycles OLED pages only. Simple debounce.
void handleButtonOLED() {
  bool state = digitalRead(PIN_BTN_OLED);
  if (btnOLEDPrev == HIGH && state == LOW) {
    oledPage = (oledPage + 1) % 4;  // 4 pages maintenant
    delay(160);
  }
  btnOLEDPrev = state;
}

// ---------- PWM LED mapping ----------
int mapThrottleToPWM(unsigned int thrUs) {
  int v = constrain((int)thrUs, 1000, 2000);
  return map(v, 1000, 2000, 0, 255);
}

// ---------- Baseline capture (blocking short) ----------
void captureBaselineOnce() {
  unsigned long t0 = millis();
  unsigned long tend = t0 + BASELINE_CAPTURE_MS;
  unsigned long sumD=0, cntD=0, sumT=0, cntT=0;
  while (millis() < tend) {
    unsigned long dlast = copyDirLastMicros();
    unsigned long tlast = copyThrLastMicros();
    if (dlast != 0) { unsigned int v = copyDirPulse(); sumD += v; cntD++; }
    if (tlast != 0) { unsigned int v = copyThrPulse(); sumT += v; cntT++; }
    delay(20);
  }
  if (cntD > 0) { baseDir = (unsigned int)(sumD / cntD); haveBaseDir = true; }
  if (cntT > 0) { baseThr = (unsigned int)(sumT / cntT); haveBaseThr = true; }
  if (!haveBaseDir) baseDir = 1500;
  if (!haveBaseThr) baseThr = 1500;
  Serial.print("Captured baseline Dir:"); Serial.print(baseDir); Serial.print(" Thr:"); Serial.println(baseThr);
}

// ---------- MPU read ----------
void readMPU() {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);  // Start at ACCEL_XOUT_H
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 14, true);
  if (Wire.available() >= 14) {
    accX = Wire.read() << 8 | Wire.read();
    accY = Wire.read() << 8 | Wire.read();
    accZ = Wire.read() << 8 | Wire.read();
    tempRaw = Wire.read() << 8 | Wire.read();
    gyroX = Wire.read() << 8 | Wire.read();
    gyroY = Wire.read() << 8 | Wire.read();
    gyroZ = Wire.read() << 8 | Wire.read();
  }
}

// ---------- Test sequence ----------
void runTestSequenceNonBlocking(unsigned long nowMs) {
  unsigned long dt = nowMs - testStartMs;
  if (dt < 800) { servoOut.writeMicroseconds(1000); digitalWrite(PIN_LED, (millis()/120)%2 ? HIGH : LOW); }
  else if (dt < 1600) { servoOut.writeMicroseconds(2000); digitalWrite(PIN_LED, (millis()/80)%2 ? HIGH : LOW); }
  else if (dt < 2200) { servoOut.writeMicroseconds(1500); digitalWrite(PIN_LED, (millis()/200)%2 ? HIGH : LOW); }
  else if (dt < 4200) { escOut.writeMicroseconds(1500 + (int)(0.05 * 500)); digitalWrite(PIN_LED, HIGH); }
  else if (dt < 6200) { escOut.writeMicroseconds(1500 - (int)(0.05 * 500)); digitalWrite(PIN_LED, HIGH); }
  else { testMode = false; escOut.writeMicroseconds(1500); servoOut.writeMicroseconds(1500); digitalWrite(PIN_LED, LOW); Serial.println("Test finished"); }
}

// ---------- OLED drawing helpers ----------
void drawAnimatedFace(Adafruit_SSD1306 &d, uint8_t frame) {
  int cx = 64, cy = 32, r = 28;
  
  // Contour tête
  d.drawCircle(cx, cy, r, SSD1306_WHITE);
  d.drawCircle(cx, cy, r-1, SSD1306_WHITE);

  // Sleeping if no power
  if (!carPowered) {
    d.drawLine(42, 28, 58, 28, SSD1306_WHITE);
    d.drawLine(70, 28, 86, 28, SSD1306_WHITE);
    d.setCursor(56, 42);
    d.setTextSize(1);
    d.setTextColor(SSD1306_WHITE);
    d.print(F("zZz"));
    return;
  }

  // Debug mode - Casque VR
  if (debugMode) {
    d.fillRect(30, 15, 68, 12, SSD1306_WHITE);
    d.fillCircle(50, 38, 5, SSD1306_WHITE);
    d.fillCircle(78, 38, 5, SSD1306_WHITE);
    d.fillCircle(50, 38, 3, SSD1306_BLACK);
    d.fillCircle(78, 38, 3, SSD1306_BLACK);
    d.fillCircle(cx, cy-20, 2, SSD1306_WHITE);
    return;
  }

  // Yeux normaux avec pupilles animées
  int pupilOffset = (frame % 60) < 30 ? -1 : 1;
  
  // Œil gauche
  d.fillCircle(52, 28, 5, SSD1306_WHITE);
  d.fillCircle(52 + pupilOffset, 28, 2, SSD1306_BLACK);
  
  // Œil droit
  d.fillCircle(76, 28, 5, SSD1306_WHITE);
  d.fillCircle(76 + pupilOffset, 28, 2, SSD1306_BLACK);
  
  // Clignotement
  if ((frame % 80) > 75) {
    d.fillRect(47, 26, 10, 4, SSD1306_BLACK);
    d.fillRect(71, 26, 10, 4, SSD1306_BLACK);
    d.drawLine(47, 28, 57, 28, SSD1306_WHITE);
    d.drawLine(71, 28, 81, 28, SSD1306_WHITE);
  }

  // Bouche - réagit à l'accélération
  long absAccX = abs((long)accX);
  long absAccY = abs((long)accY);
  
  if (absAccX > 15000L || absAccY > 15000L) {
    // Surpris
    d.drawCircle(64, 44, 6, SSD1306_WHITE);
    d.fillCircle(64, 44, 4, SSD1306_BLACK);
  } else if (serverConnected && serverMode) {
    // Sourire content (mode serveur actif)
    for (int i = 0; i < 12; ++i) {
      int x1 = cx - 14 + i*2;
      int y1 = cy + 10 + (int)(2.5 * sin((i / 12.0) * 3.14));
      d.fillCircle(x1, y1, 1, SSD1306_WHITE);
    }
  } else {
    // Sourire neutre
    for (int i = 0; i < 10; ++i) {
      int x1 = cx - 12 + i*2;
      int y1 = cy + 10 + (int)(1.5 * sin((i / 10.0) * 3.14));
      d.drawPixel(x1, y1, SSD1306_WHITE);
    }
  }
  
  // Antenne si serveur connecté
  if (serverConnected) {
    d.drawLine(cx, cy-r, cx, cy-r-5, SSD1306_WHITE);
    d.fillCircle(cx, cy-r-7, 2, SSD1306_WHITE);
  }
}

void drawBatteryIcon(Adafruit_SSD1306 &d, int levelPercent) {
  int x=4, y=4, w=22, h=10;
  d.drawRect(x,y,w,h,SSD1306_WHITE);
  d.fillRect(x+w, y+2, 2, h-4, SSD1306_WHITE);
  int innerW = max(0, (levelPercent * (w-4)) / 100);
  d.fillRect(x+2, y+2, innerW, h-4, SSD1306_WHITE);
}

void drawSignalIcon(Adafruit_SSD1306 &d, int strength) {
  int baseX = 110, baseY = 54;
  for (int i=0;i<4;i++) {
    int h = (i+1)*6;
    if (i < strength) {
      d.fillRect(baseX + i*6, baseY - h, 4, h, SSD1306_WHITE);
    } else {
      d.drawRect(baseX + i*6, baseY - h, 4, h, SSD1306_WHITE);
    }
  }
}

// ---------- OLED pages ----------
void oled_page_face(uint8_t frame) {
  if (display.width() == 0) return;
  display.clearDisplay();
  drawAnimatedFace(display, frame);
  drawBatteryIcon(display, rcBatteryLow ? 10 : 75);
  int sig = (!awaitingRX) ? 3 : 0;
  drawSignalIcon(display, sig);
  display.display();
}

void oled_page_mpu() {
  if (display.width() == 0) return;
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0,0);
  display.print(F("MPU-6500"));
  display.setCursor(0,12);
  display.print(F("Acc X: ")); display.println(accX);
  display.print(F("Acc Y: ")); display.println(accY);
  display.print(F("Acc Z: ")); display.println(accZ);
  display.setCursor(0,40);
  display.print(F("Gyr X: ")); display.println(gyroX);
  display.print(F("Gyr Y: ")); display.println(gyroY);
  display.print(F("Gyr Z: ")); display.println(gyroZ);
  display.display();
}

void oled_page_system() {
  if (display.width() == 0) return;
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0,0);
  display.print(F("SYSTEM"));
  display.setCursor(0,12);
  display.print(F("CarP: "));
  display.println(carPowered ? "ON" : "OFF");
  display.print(F("RX: "));
  display.println(awaitingRX ? "NO" : "OK");
  display.print(F("Debug: "));
  display.println(debugMode ? "YES" : "NO");
  display.display();
}

void oled_page_server() {
  if (display.width() == 0) return;
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.print(F("PC SERVER"));
  display.setCursor(0, 12);
  
  if (serverConnected) {
    display.print(F("Status: ONLINE"));
    display.setCursor(0, 24);
    display.print(F("Mode: "));
    display.print(serverMode ? "SERVER" : "RC");
    display.setCursor(0, 36);
    display.print(F("Dir: "));
    display.print(serverDir);
    display.setCursor(0, 48);
    display.print(F("Thr: "));
    display.print(serverThr);
  } else {
    display.print(F("Status: OFFLINE"));
    display.setCursor(0, 36);
    display.print(F("Waiting..."));
  }
  
  display.display();
}
// ---------- Setup ----------
void setup() {
  Serial.begin(115200);
  // ===== AJOUT: Serial1 pour ESP32 =====
  Serial1.begin(115200);
  Serial.println("Arduino Mega + ESP32 Server ready");
  randomSeed(analogRead(A1));

  pinMode(PIN_DIR_IN, INPUT);
  pinMode(PIN_THR_IN, INPUT);
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_BTN_LCD, INPUT_PULLUP);
  pinMode(PIN_BTN_OLED, INPUT_PULLUP);
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);
  pinMode(PIN_PWM_LED, OUTPUT);

  pinMode(PIN_TURN_L, OUTPUT); digitalWrite(PIN_TURN_L, LOW);
  pinMode(PIN_TURN_R, OUTPUT); digitalWrite(PIN_TURN_R, LOW);
  pinMode(PIN_BRAKE, OUTPUT);  digitalWrite(PIN_BRAKE, LOW);

  attachInterrupt(digitalPinToInterrupt(PIN_DIR_IN), dirISR, CHANGE);
  attachInterrupt(digitalPinToInterrupt(PIN_THR_IN), thrISR, CHANGE);

  servoOut.attach(PIN_SERVO_OUT);
  escOut.attach(PIN_ESC_OUT);
  servoOut.writeMicroseconds(1500);
  escOut.writeMicroseconds(1500);

  Wire.begin();

  // INIT MPU-6500 (wake + default ranges)
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B);     // PWR_MGMT_1
  Wire.write(0x00);     // Wake up MPU
  Wire.endTransmission();
  delay(100);
  Wire.beginTransmission(MPU_ADDR); Wire.write(0x1C); Wire.write(0x00); Wire.endTransmission(); // ACCEL ±2G
  Wire.beginTransmission(MPU_ADDR); Wire.write(0x1B); Wire.write(0x00); Wire.endTransmission(); // GYRO ±250dps

  // LCD init
  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcdPresent = true;

  // OLED init once
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println(F("SSD1306 allocation failed"));
  } else {
    display.clearDisplay();
    display.display();
  }

  lcdPrintLine(0, "Waiting Power...");
  lcdPrintLine(1, "Connect A0 node");

  carPowered = false;
  awaitingRX = true;
  lcdPage = 0;
  oledPage = 0;
  lastPowerSampleMs = millis();
  powerHighCount = powerLowCount = 0;
  lastNoRxSweepMs = millis();

  rcNoiseWindowStart = millis();
  rcNoiseCount = 0;
}

// ===== AJOUT: Parse commandes ESP32 =====
void parseESP32Command(String data) {
  data.trim();
  
  Serial.print("DEBUG: ESP32 sent: '");
  Serial.print(data);
  Serial.println("'");
  
  // Heartbeat PING
  if (data == "PING") {
    lastServerCommandMs = millis();
    
    if (!serverConnected) {
      serverConnected = true;
      serverMode = false;  // Heartbeat = connexion mais pas de contrôle actif
      popupMsg = "SERVER ONLINE";
      popupShown = true;
      popupStart = millis();
      Serial.println("✓ Server connected (heartbeat)!");
    }
    return;
  }
  
  // Commande de contrôle
  if (data.startsWith("CMD:")) {
    int colonPos = data.indexOf(':', 4);
    if (colonPos > 0) {
      serverDir = data.substring(4, colonPos).toInt();
      serverThr = data.substring(colonPos + 1).toInt();
      serverDir = constrain(serverDir, 1000, 2000);
      serverThr = constrain(serverThr, 1000, 2000);
      lastServerCommandMs = millis();
      
      if (!serverConnected) {
        serverConnected = true;
        popupMsg = "SERVER ONLINE";
        popupShown = true;
        popupStart = millis();
        Serial.println("✓ Server connected!");
      }
      
      // Mode serveur actif seulement si commandes reçues
      serverMode = true;
    }
  }
}

// ===== AJOUT: Envoi télémétrie ESP32 =====
void sendTelemetryToESP32() {
  unsigned int dir = dirLastPublished;
  unsigned int thr = thrLastPublished;
  float batt = (analogRead(PIN_POWER_A0) / 1023.0) * 12.6;
  
  // Format: TELEM:{dir}:{thr}:{dist}:{batt}:{rx}
  Serial1.print("TELEM:");
  Serial1.print(dir);
  Serial1.print(":");
  Serial1.print(thr);
  Serial1.print(":");
  Serial1.print(distanceCm);
  Serial1.print(":");
  Serial1.print(batt, 1);
  Serial1.print(":");
  Serial1.print(awaitingRX ? 0 : 1);
  Serial1.println();
}

// ---------- Loop ----------
void loop() {
  // sample MPU early
  readMPU();

 // ===== AJOUT: Lecture ESP32 =====
  while (Serial1.available()) {
    char c = Serial1.read();
    if (c == '\n') {
      if (esp32Buffer.length() > 0) {
        parseESP32Command(esp32Buffer);
        esp32Buffer = "";
      }
    } else if (c != '\r') {
      esp32Buffer += c;
    }
  }

  // Timeout serveur
  if (serverConnected && (millis() - lastServerCommandMs > SERVER_TIMEOUT_MS)) {
    serverConnected = false;
    serverMode = false;
    Serial.println("Server disconnected");
  }

  unsigned long nowMs = millis();
  unsigned long nowUs = micros();

  // ---------- OLED animation update (non-blocking) ----------
  static unsigned long lastFrame = 0;
  static uint8_t frame = 0;
  if (nowMs - lastFrame > 100) {
    lastFrame = nowMs;
    frame++;
    if (oledPage == 0) oled_page_face(frame);
   else if (oledPage == 1) oled_page_mpu();
   else if (oledPage == 2) oled_page_system();
   else oled_page_server();  // Page 3
  }

  // Serial commands (non-blocking)
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n'); cmd.trim(); cmd.toUpperCase();
    if (cmd == "RX") { rxSerialOverride = true; rxSerialOverrideTs = nowMs; awaitingRX = false; Serial.println("RX override ON"); }
    else if (cmd == "NO_RX") { rxSerialOverride = false; Serial.println("NO_RX -> override cleared"); }
    else if (cmd == "DANSE" || cmd == "DANCE") { danceMode = true; danceStartMs = nowMs; Serial.println("Dance start"); }
    else if (cmd == "TEST") { if (!testMode) { testMode = true; testStartMs = nowMs; Serial.println("Test start"); } }
    else if (cmd == "DEBUG_OFF") { debugMode = false; rxSerialOverride = false; Serial.println("DEBUG OFF"); popupMsg="DEBUG OFF"; popupShown=true; popupStart=nowMs; }
  }

  // ---------- Power sampling & debounce ----------
  if (nowMs - lastPowerSampleMs >= POWER_SAMPLE_MS) {
    lastPowerSampleMs = nowMs;
    int a = analogRead(PIN_POWER_A0);
    if (a >= POWER_HIGH_THR) { powerHighCount++; powerLowCount = 0; }
    else if (a <= POWER_LOW_THR) { powerLowCount++; powerHighCount = 0; }
    else { if (powerHighCount>0) powerHighCount--; if (powerLowCount>0) powerLowCount--; }

    if (!carPowered && powerHighCount >= POWER_DEBOUNCE_COUNT) {
      carPowered = true;
      Serial.print("Power ON (A0="); Serial.print(a); Serial.println(") - debounced");
      lcdPrintLine(0, "Power detected...");
      lcdPrintLine(1, "Capturing baseline");
      captureBaselineOnce();
      startBoot(nowMs);
    } else if (carPowered && powerLowCount >= POWER_DEBOUNCE_COUNT) {
      carPowered = false;
      awaitingRX = true;
      rxSerialOverride = false;
      debugMode = false; // clear debug mode on power loss
      servoOut.writeMicroseconds(1500);
      escOut.writeMicroseconds(1500);
      lcdPrintLine(0, "Waiting Power...");
      lcdPrintLine(1, "Connect A0 node");
      Serial.print("Power OFF (A0="); Serial.print(a); Serial.println(")");
    }
  }

  // if not powered -> allow long-press override on LCD button
  if (!carPowered) {
    handleButtons();
    if (popupShown && (nowMs - popupStart) > POPUP_TIME_MS) popupShown = false;
    delay(20);
    return;
  }

  // handle buttons normally
  handleButtons();

  // process boot if active
  if (booting) { processBoot(nowMs); return; }

  // ---------- HC-SR04 periodic measure ----------
  if (nowMs - lastPingMs >= PING_INTERVAL) {
    lastPingMs = nowMs;
    int d = pingMedian3();
    if (d > 0) {
      if (d != distanceCm) distanceCm = d;
      if (distanceCm > 0 && distanceCm <= OBSTACLE_CM) { closeCount++; clearCount = 0; if (closeCount >= N_CLOSE && !obstacleStop) { obstacleStop = true; Serial.println("Obstacle -> STOP"); } }
      else if (distanceCm < 0 || distanceCm >= CLEAR_CM) { clearCount++; closeCount = 0; if (clearCount >= N_CLEAR && obstacleStop) { obstacleStop = false; Serial.println("Obstacle cleared"); } }
    }
  }

  // ---------- channel freshness ----------
  unsigned long dirLast = copyDirLastMicros();
  unsigned long dirPrev = copyDirPrevMicros();
  unsigned long thrLast = copyThrLastMicros();
  unsigned long thrPrev = copyThrPrevMicros();

  bool dirFresh = channelFresh(dirLast, dirPrev, nowMs);
  bool thrFresh = channelFresh(thrLast, thrPrev, nowMs);

  // RC battery low detection: count "weird" events (invalid pulses, big jumps)
  unsigned int tmpDir = copyDirPulse();
  unsigned int tmpThr = copyThrPulse();
  bool weird = false;
  if (dirFresh && (tmpDir < 1000 || tmpDir > 2000)) weird = true;
  if (thrFresh && (tmpThr < 1000 || tmpThr > 2000)) weird = true;
  if (abs((int)tmpDir - (int)dirLastPublished) > 400) weird = true;
  if (abs((int)tmpThr - (int)thrLastPublished) > 400) weird = true;

  if (nowMs - rcNoiseWindowStart > RC_NOISE_WINDOW_MS) { rcNoiseWindowStart = nowMs; rcNoiseCount = 0; }
  if (weird) rcNoiseCount++;
  if (!rcBatteryLow && rcNoiseCount >= RC_NOISE_THRESHOLD) {
    rcBatteryLow = true;
    popupMsg = "RC BATTERY LOW";
    popupShown = true; popupStart = nowMs;
    Serial.println("Warning: RC battery low suspected (noisy signals)");
  }

  // auto clear serial RX override (but DO NOT auto-clear if debugMode is active)
  if (rxSerialOverride && !debugMode) {
    if (!dirFresh && !thrFresh && (nowMs - rxSerialOverrideTs > RX_OVERRIDE_TIMEOUT_MS)) { rxSerialOverride = false; Serial.println("RX override auto-cleared"); }
  }

  // ---------- decide rxPresent / awaitingRX ----------
  bool rxPresent;
  if (debugMode) {
    rxPresent = true;
    rxSerialOverride = true;
  } else if (rxSerialOverride) {
    rxPresent = true;
  } else {
    if (STRICT_RX_REQUIRE_DIR) rxPresent = dirFresh;
    else rxPresent = dirFresh || thrFresh;
  }
  awaitingRX = !rxPresent;

  // ---------- Dance / Test ----------
  if (danceMode) {
    if (nowMs - danceStartMs >= 10000UL) { danceMode = false; servoOut.writeMicroseconds(1500); escOut.writeMicroseconds(1500); Serial.println("Dance end"); }
    else if ((nowMs % 150) < 10) { unsigned int r = (unsigned int)random(1000,2000); servoOut.writeMicroseconds(r); escOut.writeMicroseconds(1500); }
  }

  if (testMode) {
    runTestSequenceNonBlocking(nowMs);
  }

  // ---------- movement detection for LED ----------
  unsigned int dirNow = tmpDir;
  unsigned int thrNow = tmpThr;
  bool movement = (abs((int)dirNow - (int)dirLastPublished) > (int)MOVEMENT_DELTA_US)
               || (abs((int)thrNow - (int)thrLastPublished) > (int)MOVEMENT_DELTA_US);
  if (movement) { lastMovementMs = nowMs; dirLastPublished = dirNow; thrLastPublished = thrNow; }

  // ---------- no-RX sweep ----------
  checkNoRxSweep(nowMs);

  // ---------- outputs forwarding + obstacle stop ----------
  // IMPORTANT: if awaitingRX OR debugMode -> force ESC+SERVO to 1500 to avoid motor spinning alone.
  int finalDir = 1500;
  int finalThr = 1500;

 if (serverMode && serverConnected) {
  finalDir = serverDir;
  finalThr = serverThr;
} else if (!awaitingRX && !debugMode && !danceMode && !testMode) {
  if (dirFresh) finalDir = dirNow;
  if (thrFresh) finalThr = thrNow;
}

servoOut.writeMicroseconds(finalDir);
escOut.writeMicroseconds(finalThr);

  // ---------- LED D13 handling ----------
  if (booting) {
    // handled in processBoot
  } else if (awaitingRX) {
    static unsigned long lastBlink = 0; static bool blinkState = false;
    if (nowMs - lastBlink > 420) { lastBlink = nowMs; blinkState = !blinkState; digitalWrite(PIN_LED, blinkState?HIGH:LOW); }
  } else {
    if (nowMs - lastMovementMs <= MOVEMENT_HOLD_MS) digitalWrite(PIN_LED, HIGH);
    else digitalWrite(PIN_LED, LOW);
  }

  // ---------- PWM LED for throttle ----------
  int pwmVal = 0;
  if (thrNow >= VALID_MIN_US && thrNow <= VALID_MAX_US) pwmVal = mapThrottleToPWM(thrNow);
  else pwmVal = 0;
  analogWrite(PIN_PWM_LED, pwmVal);

  // ---------- turn signals & brake lights ----------
  int neutralDir = haveBaseDir ? (int)baseDir : 1500;
  int leftThreshold = neutralDir - 80;
  int rightThreshold = neutralDir + 80;
  bool turningLeft = dirNow < leftThreshold && dirFresh;
  bool turningRight = dirNow > rightThreshold && dirFresh;

  if (turningLeft) {
    if (nowMs - lastTurnBlink > TURN_BLINK_MS) { lastTurnBlink = nowMs; turnState = !turnState; }
    digitalWrite(PIN_TURN_L, turnState ? HIGH : LOW);
    digitalWrite(PIN_TURN_R, LOW);
  } else if (turningRight) {
    if (nowMs - lastTurnBlink > TURN_BLINK_MS) { lastTurnBlink = nowMs; turnState = !turnState; }
    digitalWrite(PIN_TURN_R, turnState ? HIGH : LOW);
    digitalWrite(PIN_TURN_L, LOW);
  } else {
    digitalWrite(PIN_TURN_L, LOW);
    digitalWrite(PIN_TURN_R, LOW);
    turnState = false;
  }

  if (thrFresh && thrNow < 1495) digitalWrite(PIN_BRAKE, HIGH);
  else digitalWrite(PIN_BRAKE, LOW);

  // ---------- LCD & Serial updates ----------
  if (nowMs - lastSerialPrint >= SERIAL_PRINT_INTERVAL) {
    lastSerialPrint = nowMs;
    Serial.print(dirNow); Serial.print(","); Serial.print(thrNow); Serial.print(","); Serial.print(distanceCm);
    Serial.print(",rx:"); Serial.print(awaitingRX?0:1);
    Serial.print(",rcLow:"); Serial.print(rcBatteryLow?1:0);
    Serial.print(",carP:"); Serial.print(carPowered?1:0);
    Serial.print(",btnL:"); Serial.print(btnLCDLongHandled?1:0);
    Serial.println();

    // popup override
    if (popupShown) {
      lcdPrintLine(0, "!!! ALERT !!!");
      lcdPrintLine(1, popupMsg);
      lcdPrintLine(2, "                ");
      lcdPrintLine(3, "                ");
      if (nowMs - popupStart > POPUP_TIME_MS) popupShown = false;
    } else {
      if (!carPowered) {
        lcdPrintLine(0, "Waiting Power...");
        lcdPrintLine(1, "Connect A0 node");
        lcdPrintLine(2, "Hold BTN to skip");
        lcdPrintLine(3, "                ");
      } else if (booting) {
        // processBoot handles LCD
      } else if (testMode) {
        lcdPrintLine(0, "TEST EN COURS");
        lcdPrintLine(1, "Ne pas interompre");
        lcdPrintLine(2, "Sequence active");
        lcdPrintLine(3, "                ");
      } else if (awaitingRX) {
        lcdPrintLine(0, "Waiting RX...");
        lcdPrintLine(1, "Hold BTN to skip");
        lcdPrintLine(2, rcBatteryLow ? "RC BATTERY LOW!" : "                ");
        lcdPrintLine(3, "A0:" + String(analogRead(PIN_POWER_A0)));
      } else {
        // LCD pages
        if (lcdPage == 0) {
          lcdPrintLine(0, "STATUS");
          lcdPrintLine(1, String("Dir:") + (dirFresh? "OK ":"No ") + " Thr:" + (thrFresh? "OK":"No "));
          lcdPrintLine(2, String("RX:") + (awaitingRX? "No":"OK") + (rcBatteryLow? " RCLow":""));
          lcdPrintLine(3, String("Dist:") + (distanceCm<0? "--":String(distanceCm) + "cm"));
        } else if (lcdPage == 1) {
          lcdPrintLine(0, "PWM RAW (us)");
          lcdPrintLine(1, "Dir:" + String(dirNow));
          lcdPrintLine(2, "Thr:" + String(thrNow));
          lcdPrintLine(3, "BaseD:" + String(baseDir) + " BThr:" + String(baseThr));
        } else if (lcdPage == 2) {
          String dstr = (distanceCm < 0) ? "--cm" : (String(distanceCm) + "cm");
          lcdPrintLine(0, "SENSORS");
          lcdPrintLine(1, "Distance:" + dstr);
          lcdPrintLine(2, "Obstacle:" + String(obstacleStop? "YES":"NO "));
          int pct = map(thrNow, 1000, 2000, 0, 100);
          lcdPrintLine(3, "Thr%:" + String(pct) + "%");
        }
      }
    }
    // Envoi télémétrie ESP32
 static unsigned long lastTelemSent = 0;
 if (nowMs - lastTelemSent >= 200) {
  lastTelemSent = nowMs;
  sendTelemetryToESP32();
}
  }

  delay(5);
} // end loop
