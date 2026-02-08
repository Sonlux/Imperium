# ESP32 Audio Node - Quick Start Guide

## ✅ Installation Complete!

ESP-IDF v5.1.2 has been installed successfully on your Raspberry Pi.

## 📁 Project Structure
```
/home/imperium/Imperium/esp32-audio-node/
├── main/
│   ├── main.cpp              - Entry point & WiFi setup
│   ├── config.h              - Configuration (WiFi, MQTT, pins)
│   ├── i2s_audio.cpp         - I2S microphone capture
│   ├── mqtt_handler.cpp      - MQTT client
│   └── policy_handler.cpp    - Imperium policy commands
├── CMakeLists.txt            - Build configuration
└── README.md                 - Full documentation
```

## 🔧 Before Building

**IMPORTANT**: Edit `main/config.h` and update:
```cpp
#define WIFI_SSID         "YourWiFiNetwork"      // Your WiFi name
#define WIFI_PASSWORD     "YourPassword"         // Your WiFi password
#define MQTT_BROKER_URI   "mqtt://192.168.1.XX:1883"  // Your Raspberry Pi IP
```

Find your Raspberry Pi IP:
```bash
hostname -I | awk '{print $1}'
```

## 🚀 Build & Flash Commands

### 1. Setup Environment
```bash
cd /home/imperium/Imperium/esp32-audio-node
source ~/esp/esp-idf/export.sh
```

### 2. Build Firmware
```bash
idf.py build
```

### 3. Flash to ESP32
```bash
# Find USB port (usually /dev/ttyUSB0 or /dev/ttyACM0)
ls /dev/tty*

# Flash firmware
idf.py -p /dev/ttyUSB0 flash

# Or flash and monitor serial output
idf.py -p /dev/ttyUSB0 flash monitor
```

### 4. Monitor Serial Output
```bash
idf.py -p /dev/ttyUSB0 monitor

# Exit monitor: Ctrl+]
```

## 🧪 Testing

### 1. Check Device Online
```bash
mosquitto_sub -h localhost -t 'iot/esp32-audio-1/status' -v
```

Expected output:
```
iot/esp32-audio-1/status {"device_id":"esp32-audio-1","status":"online"}
```

### 2. View All Topics
```bash
mosquitto_sub -h localhost -t 'iot/esp32-audio-1/#' -v
```

### 3. Send Control Command
```bash
# Change QoS to 0
mosquitto_pub -h localhost -t 'iot/esp32-audio-1/control' \
  -m '{"command":"SET_QOS","qos":0}'

# Change sample rate to 8kHz
mosquitto_pub -h localhost -t 'iot/esp32-audio-1/control' \
  -m '{"command":"SET_SAMPLE_RATE","sample_rate":8000}'
```

### 4. Check Prometheus Metrics
```bash
# Get ESP32 IP from serial monitor, then:
curl http://<esp32-ip>:8080/metrics
```

## 🔌 Hardware Wiring

```
ESP32 Pin    →    I2S Microphone (INMP441)
GPIO25       →    SCK  (Serial Clock)
GPIO33       →    WS   (Word Select)
GPIO32       →    SD   (Serial Data)
3.3V         →    VDD
GND          →    GND
              →    L/R (connect to GND for left channel)
```

## 🐛 Troubleshooting

### Error: Port not found
```bash
# Check connected devices
ls /dev/ttyUSB* /dev/ttyACM*

# Add user to dialout group
sudo usermod -a -G dialout $USER
# Then logout and login again
```

### Error: Permission denied
```bash
sudo chmod 666 /dev/ttyUSB0
```

### WiFi not connecting
- Check SSID/password in config.h
- Make sure ESP32 is within WiFi range
- Try 2.4GHz network (ESP32 doesn't support 5GHz)

### MQTT not connecting
- Verify Raspberry Pi IP address
- Check mosquitto is running: `sudo systemctl status mosquitto`
- Test with mosquitto_pub/sub from another device

### No audio output
- Check I2S wiring (especially GND connections)
- Verify L/R pin is tied to GND or VDD
- Monitor serial for "I2S read error" messages
- Try different GPIO pins if needed

## 📊 Expected Performance

| Metric | Value |
|--------|-------|
| Build Time | ~2-3 minutes (first time) |
| Flash Time | ~30 seconds |
| Boot Time | ~5 seconds |
| MQTT Connect | <3 seconds |
| Audio Latency | 30-80ms |
| Bandwidth | 256 Kbps @ 16kHz |
| CPU Usage | 30-40% |
| Memory Usage | ~120KB |

## 📚 Next Steps

1. **Build the firmware**: `idf.py build`
2. **Update config.h** with your WiFi credentials
3. **Connect ESP32** via USB
4. **Flash firmware**: `idf.py -p /dev/ttyUSB0 flash monitor`
5. **Watch serial output** for successful WiFi/MQTT connection
6. **Test MQTT** with mosquitto_sub
7. **Integrate with Imperium** (see main README.md)

## 📖 Documentation

- [Main README](README.md) - Full documentation
- [ESP-IDF Programming Guide](https://docs.espressif.com/projects/esp-idf/en/v5.1.2/)
- [INMP441 Datasheet](https://www.invensense.com/products/digital/inmp441/)

---

**Status**: ✅ ESP-IDF Installed | ⏳ Configuration Needed | ⏳ Build Pending
