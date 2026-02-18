# ESP32 MH-Z19 CO2 Sensor - Complete Setup Summary

## ✅ Project Created Successfully

**Location:** `/home/imperium/Imperium/esp32-mhz19-node/`

## 📁 Project Structure

```
esp32-mhz19-node/
├── main/
│   ├── main.c              # Main application
│   ├── mhz19.c/h           # MH-Z19 sensor driver
│   ├── wifi_handler.c/h    # WiFi connection management
│   ├── mqtt_handler.c/h    # MQTT communication
│   ├── config.h            # Configuration settings
│   └── CMakeLists.txt      # Build configuration
├── CMakeLists.txt          # Project build file
├── sdkconfig.defaults      # ESP-IDF default config
├── README.md               # Full documentation
├── QUICKSTART.md           # Quick setup guide
├── INTEGRATION.md          # Imperium integration
├── TROUBLESHOOTING.md      # Debug guide
├── setup_esp.sh            # Configuration script
├── flash.sh                # Quick flash script
└── build_and_flash.sh      # Complete build process
```

## 🔌 Hardware Wiring

```
MH-Z19 Sensor    →    ESP32 Board
═════════════════════════════════
VCC (Pin 6)      →    5V (VIN)
GND (Pin 7)      →    GND
TX (Pin 2)       →    GPIO16 (RX2)
RX (Pin 3)       →    GPIO17 (TX2)
```

**⚠️ Critical:**
- MH-Z19 requires 5V (connect to VIN, not 3.3V)
- TX connects to RX, RX connects to TX
- Wait 3 minutes for sensor warm-up

## 🚀 Quick Start (One Command)

```bash
cd /home/imperium/Imperium/esp32-mhz19-node
./build_and_flash.sh
```

This script will:
1. ✅ Check ESP-IDF installation
2. ✅ Detect ESP32 serial port
3. ✅ Configure WiFi/MQTT (interactive)
4. ✅ Build firmware
5. ✅ Flash to ESP32
6. ✅ Start serial monitor (optional)

## 📝 Manual Build Process

### Step 1: Install ESP-IDF (if not installed)
```bash
sudo apt-get install git wget flex bison gperf python3 python3-pip \
    python3-venv cmake ninja-build ccache libffi-dev libssl-dev dfu-util libusb-1.0-0

mkdir -p ~/esp
cd ~/esp
git clone --recursive https://github.com/espressif/esp-idf.git
cd esp-idf
./install.sh esp32
source export.sh
```

### Step 2: Configure Project
```bash
cd /home/imperium/Imperium/esp32-mhz19-node
./setup_esp.sh

# Or edit main/config.h manually:
# - WIFI_SSID
# - WIFI_PASSWORD
# - MQTT_BROKER_URL
# - DEVICE_ID
```

### Step 3: Build Firmware
```bash
source ~/esp/esp-idf/export.sh  # If not in current session
idf.py build
```

### Step 4: Flash to ESP32
```bash
# Connect ESP32 via USB
idf.py -p /dev/ttyUSB0 flash

# Monitor output
idf.py -p /dev/ttyUSB0 monitor
# Press Ctrl+] to exit
```

## 📊 Expected Serial Output

```
I (xxx) MAIN: ═══════════════════════════════════
I (xxx) MAIN:   ESP32 MH-Z19 CO2 Sensor Node
I (xxx) MAIN:   Device: esp32-mhz19-1
I (xxx) MAIN:   Version: 1.0.0
I (xxx) MAIN: ═══════════════════════════════════
I (xxx) MHZ19: MH-Z19 initialized successfully (warm-up: 3 minutes)
I (xxx) WIFI: WiFi initialization finished. Connecting to YourWiFi...
I (xxx) WIFI: Connected to AP SSID:YourWiFi
I (xxx) WIFI: Got IP:192.168.1.XXX
I (xxx) MQTT: MQTT connected
I (xxx) SENSOR: Sensor warming up... (0/180000 ms)
...
I (xxx) SENSOR: Sensor warm-up complete, starting measurements
I (xxx) SENSOR: CO2: 450 ppm, Temp: 23°C (read #1)
```

## 🧪 Testing

### 1. Verify MQTT Telemetry
```bash
mosquitto_sub -h 192.168.1.100 -v -t "imperium/devices/esp32-mhz19-1/telemetry"
```

**Expected output:**
```json
{
  "device_id": "esp32-mhz19-1",
  "timestamp": 1707654321,
  "co2_ppm": 450,
  "temperature": 23,
  "sensor_status": "ready",
  "rssi": -56
}
```

### 2. Send MQTT Command
```bash
mosquitto_pub -h 192.168.1.100 \
    -t "imperium/devices/esp32-mhz19-1/control" \
    -m '{"command":"GET_INFO"}'
```

### 3. Test Imperium Intent
```bash
TOKEN=$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin"}' | \
    python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

curl -X POST http://localhost:5000/api/v1/intents \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"description":"Set publish interval to 10 seconds for esp32-mhz19-1"}'
```

## 🎯 Features Implemented

### ✅ Sensor Capabilities
- [x] Real-time CO2 measurement (0-5000 ppm)
- [x] Temperature reading
- [x] Automatic warm-up detection (3 minutes)
- [x] Configurable detection range (2000/5000/10000 ppm)
- [x] Zero point calibration (400 ppm)
- [x] Automatic Baseline Correction (ABC)

### ✅ Communication
- [x] WiFi connection with auto-reconnect
- [x] MQTT publish/subscribe
- [x] JSON telemetry format
- [x] Command handling via MQTT
- [x] Status reporting

### ✅ Control Features
- [x] Configurable publish interval (1s - 5min)
- [x] Remote calibration commands
- [x] Detection range adjustment
- [x] ABC enable/disable
- [x] Sensor info query

### ✅ System Features
- [x] LED status indicator
- [x] Watchdog timer
- [x] UART error handling
- [x] Memory management
- [x] Logging system

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| **README.md** | Complete technical documentation |
| **QUICKSTART.md** | Fast setup guide |
| **INTEGRATION.md** | Imperium system integration |
| **TROUBLESHOOTING.md** | Debug and problem-solving |

## 🔧 Configuration Options

Edit `main/config.h` to customize:

```c
// WiFi
#define WIFI_SSID "YourWiFiSSID"
#define WIFI_PASSWORD "YourWiFiPassword"

// MQTT
#define MQTT_BROKER_URL "mqtt://192.168.1.100"
#define DEVICE_ID "esp32-mhz19-1"

// Sensor
#define MHZ19_DEFAULT_RANGE MHZ19_RANGE_5000
#define MHZ19_ABC_ENABLED true

// Publishing
#define DEFAULT_PUBLISH_INTERVAL_MS 5000
```

## 🌐 MQTT Topics

| Topic | Type | Description |
|-------|------|-------------|
| `imperium/devices/esp32-mhz19-1/telemetry` | Publish | Sensor data |
| `imperium/devices/esp32-mhz19-1/status` | Publish | Device status |
| `imperium/devices/esp32-mhz19-1/control` | Subscribe | Control commands |
| `imperium/devices/esp32-mhz19-1/config` | Subscribe | Configuration |

## 🎛️ Supported Commands

```json
{"command": "SET_PUBLISH_INTERVAL", "interval_ms": 10000}
{"command": "CALIBRATE_ZERO"}
{"command": "SET_DETECTION_RANGE", "range_ppm": 5000}
{"command": "SET_ABC", "enabled": true}
{"command": "GET_INFO"}
```

## ⚙️ Imperium Integration

Device registered in `config/devices.yaml`:

```yaml
esp32-mhz19-1:
  type: co2_sensor
  model: MH-Z19B
  capabilities:
    - mqtt
    - co2_monitoring
    - temperature
    - calibration
  mqtt_topics:
    telemetry: "imperium/devices/esp32-mhz19-1/telemetry"
    control: "imperium/devices/esp32-mhz19-1/control"
```

## 🚨 Troubleshooting Quick Reference

| Problem | Solution |
|---------|----------|
| Sensor not responding | Check wiring, verify 5V power, wait 3min warm-up |
| Flash failed | Press BOOT button, check USB cable, verify port permissions |
| WiFi not connecting | Check SSID/password, use 2.4GHz network |
| MQTT not connecting | Verify broker IP, check port 1883, test with mosquitto |
| Inaccurate readings | Calibrate in fresh air, enable ABC, wait 24h for best accuracy |
| Build errors | Source ESP-IDF: `source ~/esp/esp-idf/export.sh` |

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed solutions.

## 📈 Air Quality Reference

| CO2 Level | Air Quality | Action |
|-----------|-------------|--------|
| < 400 ppm | Outdoor | Normal |
| 400-800 ppm | Good | No action needed |
| 800-1000 ppm | Acceptable | Monitor |
| 1000-1500 ppm | Poor | Increase ventilation |
| 1500-2000 ppm | Very Poor | Open windows |
| > 2000 ppm | Dangerous | Evacuate and ventilate |

## 🔗 Useful Commands

```bash
# Monitor real-time
idf.py -p /dev/ttyUSB0 monitor

# Rebuild and flash
idf.py build flash monitor

# Erase flash (if corrupted)
esptool.py --port /dev/ttyUSB0 erase_flash

# Check device info
esptool.py --port /dev/ttyUSB0 chip_id

# Monitor MQTT
mosquitto_sub -h BROKER_IP -v -t "imperium/devices/+/telemetry"
```

## 📞 Support

- **Hardware Issues**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Integration**: See [INTEGRATION.md](INTEGRATION.md)
- **ESP-IDF**: https://docs.espressif.com/projects/esp-idf/
- **MH-Z19 Datasheet**: https://www.winsen-sensor.com/d/files/MH-Z19B.pdf

## ✨ Next Steps

1. ✅ **Build and flash** firmware to ESP32
2. ✅ **Verify operation** via serial monitor
3. ✅ **Test MQTT** communication
4. ✅ **Submit intents** via Imperium API
5. ✅ **Set up monitoring** in Grafana
6. ✅ **Configure alerts** for high CO2

---

**Project Status:** ✅ **READY TO BUILD**

Run `./build_and_flash.sh` to get started!
