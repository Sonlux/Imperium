# ESP32 MH-Z19 Quick Start Guide

## 1. Hardware Setup

### Connect MH-Z19 to ESP32:
```
MH-Z19         ESP32
──────────────────────
VCC (Pin 6)  → 5V (VIN)
GND (Pin 7)  → GND
TX (Pin 2)   → GPIO16
RX (Pin 3)   → GPIO17
```

**⚠️ Important:**
- Use 5V power (VIN pin), NOT 3.3V
- Double-check TX/RX connections
- Keep wires short (<20cm)

## 2. Install ESP-IDF

```bash
# Install prerequisites
sudo apt-get install git wget flex bison gperf python3 python3-pip python3-venv \
    cmake ninja-build ccache libffi-dev libssl-dev dfu-util libusb-1.0-0

# Clone ESP-IDF
mkdir -p ~/esp
cd ~/esp
git clone --recursive https://github.com/espressif/esp-idf.git
cd esp-idf
./install.sh esp32

# Set up environment (add to ~/.bashrc)
alias get_idf='. $HOME/esp/esp-idf/export.sh'
```

## 3. Configure & Build

```bash
cd /home/imperium/Imperium/esp32-mhz19-node

# Set up environment
get_idf  # or: source ~/esp/esp-idf/export.sh

# Configure WiFi and MQTT
./setup_esp.sh

# Build firmware
idf.py build
```

## 4. Flash to ESP32

```bash
# Find serial port
ls /dev/ttyUSB*  # Usually /dev/ttyUSB0

# Flash firmware
idf.py -p /dev/ttyUSB0 flash

# Monitor output
idf.py -p /dev/ttyUSB0 monitor

# Exit monitor: Ctrl+]
```

## 5. Quick Flash Script

```bash
chmod +x flash.sh
./flash.sh /dev/ttyUSB0
```

## 6. Verify Operation

Watch for these log messages:
```
I (xxx) MAIN: ═══════════════════════════════════
I (xxx) MAIN:   ESP32 MH-Z19 CO2 Sensor Node
I (xxx) MAIN: ═══════════════════════════════════
I (xxx) MHZ19: MH-Z19 initialized successfully
I (xxx) WIFI: Connected to AP SSID:YourWiFi
I (xxx) MQTT: MQTT connected
I (xxx) SENSOR: Sensor warm-up complete
I (xxx) SENSOR: CO2: 450 ppm, Temp: 23°C
```

## 7. Test MQTT Communication

```bash
# Subscribe to telemetry
mosquitto_sub -h 192.168.1.100 -t "imperium/devices/esp32-mhz19-1/telemetry"

# Send test command
mosquitto_pub -h 192.168.1.100 \
    -t "imperium/devices/esp32-mhz19-1/control" \
    -m '{"command":"GET_INFO"}'
```

## 8. Common Issues

### Sensor Not Responding
- Check wiring (TX/RX swapped?)
- Verify 5V power
- Wait 3 minutes for warm-up

### Flash Failed
- Press BOOT button while connecting
- Check USB cable (data cable, not charge-only)
- Try different USB port
- Check permissions: `sudo usermod -a -G dialout $USER`

### WiFi Not Connecting
- Verify SSID/password in config.h
- Check 2.4GHz network (ESP32 doesn't support 5GHz)
- Ensure router is in range

### MQTT Not Connecting
- Verify broker IP address
- Check port 1883 is open
- Test with: `mosquitto_pub -h BROKER_IP -t test -m "hello"`

## 9. Calibration

### Zero Point (Fresh Air)
Place sensor outdoors for 20 minutes, then:
```bash
mosquitto_pub -h 192.168.1.100 \
    -t "imperium/devices/esp32-mhz19-1/control" \
    -m '{"command":"CALIBRATE_ZERO"}'
```

## 10. Integration with Imperium

```bash
# Test intent submission
curl -X POST http://localhost:5000/api/v1/intents \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"description":"Set publish interval to 10 seconds for esp32-mhz19-1"}'
```

## Next Steps

- See [README.md](README.md) for full documentation
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed debugging
- Review [WIRING_DIAGRAM.png](docs/wiring.png) for reference
