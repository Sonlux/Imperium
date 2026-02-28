# ESP32 MH-Z19 CO2 Sensor Node

ESP32-based CO2 monitoring node using MH-Z19 sensor for Imperium Intent-Based Networking system.

## Hardware Requirements

- **ESP32 Development Board** (ESP32-DevKitC, ESP32-WROOM-32, or similar)
- **MH-Z19 CO2 Sensor** (MH-Z19B or MH-Z19C recommended)
- **Jumper wires**
- **USB cable** for programming
- **Power supply**: 5V via USB or external

## MH-Z19 Sensor Specifications

- **Measurement Range**: 0-5000 ppm (MH-Z19B), 0-10000 ppm (MH-Z19C)
- **Accuracy**: ±(50ppm + 5% reading value)
- **Warm-up Time**: 3 minutes
- **Response Time**: < 60 seconds
- **Operating Voltage**: 4.5V - 5.5V
- **Current Draw**: < 18mA (average)
- **Interface**: UART (9600 baud)
- **Calibration**: Automatic baseline correction (ABC) enabled by default

## Wiring Diagram

```
MH-Z19 Sensor    →    ESP32
─────────────────────────────
VCC (Pin 6)      →    5V (VIN)
GND (Pin 7)      →    GND
TX (Pin 2)       →    GPIO16 (RX2)
RX (Pin 3)       →    GPIO17 (TX2)

Optional:
HD (Pin 1)       →    Not connected (High Definition output, PWM)
```

**Important Notes:**
- MH-Z19 requires 5V power (connect to VIN, not 3.3V)
- TX/RX pins use 3.3V logic (safe for ESP32)
- Do NOT connect HD pin unless using PWM mode

## Pin Configuration

| Function | GPIO | Default |
|----------|------|---------|
| UART2 RX | 16   | RX from MH-Z19 TX |
| UART2 TX | 17   | TX to MH-Z19 RX |
| Status LED | 2   | Built-in LED |

## Features

- **Real-time CO2 monitoring** (ppm)
- **Temperature reading** (from internal sensor)
- **MQTT telemetry publishing** (configurable interval)
- **Automatic calibration** (ABC logic)
- **Manual calibration** (zero point, span point)
- **Detection range adjustment** (0-2000, 0-5000, 0-10000 ppm)
- **Intent-based controls** via MQTT
- **OTA firmware updates**
- **WiFi reconnection handling**

## MQTT Topics

### Subscribe (Commands)
- `imperium/devices/esp32-mhz19-{N}/config` - Configuration updates
- `imperium/devices/esp32-mhz19-{N}/control` - Control commands

### Publish (Telemetry)
- `imperium/devices/esp32-mhz19-{N}/telemetry` - Sensor data
- `imperium/devices/esp32-mhz19-{N}/status` - Device status

## Telemetry Data Format

```json
{
  "device_id": "esp32-mhz19-1",
  "timestamp": 1707654321,
  "co2_ppm": 450,
  "temperature": 23.5,
  "sensor_status": "ready",
  "abc_enabled": true,
  "detection_range": 5000,
  "rssi": -56
}
```

## Control Commands

### Set Publishing Interval
```json
{
  "command": "SET_PUBLISH_INTERVAL",
  "interval_ms": 5000
}
```

### Calibrate Zero Point (400 ppm fresh air)
```json
{
  "command": "CALIBRATE_ZERO"
}
```

### Set Detection Range
```json
{
  "command": "SET_DETECTION_RANGE",
  "range_ppm": 5000
}
```
Options: 2000, 5000, 10000

### Enable/Disable ABC
```json
{
  "command": "SET_ABC",
  "enabled": true
}
```

### Read Sensor Info
```json
{
  "command": "GET_INFO"
}
```

## Build & Flash

### Prerequisites
```bash
# Install ESP-IDF
sudo apt-get install git wget flex bison gperf python3 python3-pip python3-venv cmake ninja-build ccache libffi-dev libssl-dev dfu-util libusb-1.0-0

# Clone ESP-IDF (if not already installed)
mkdir -p ~/esp
cd ~/esp
git clone --recursive https://github.com/espressif/esp-idf.git
cd esp-idf
./install.sh esp32
```

### Quick Build
```bash
cd /home/imperium/Imperium/esp32-mhz19-node

# Configure WiFi and MQTT settings
./setup_esp.sh

# Build firmware
idf.py build

# Flash to ESP32
idf.py -p /dev/ttyUSB0 flash

# Monitor output
idf.py -p /dev/ttyUSB0 monitor
```

### Configuration
Edit `main/config.h` or use `idf.py menuconfig`:
- WiFi SSID/Password
- MQTT Broker IP
- Device ID
- Default publish interval
- Calibration settings

## Calibration Procedure

### Zero Point Calibration (400 ppm)
1. Place sensor in **fresh outdoor air** for 20+ minutes
2. Send calibration command via MQTT or press calibration button
3. Sensor will store 400 ppm as baseline

### Span Point Calibration (Optional)
For higher accuracy, calibrate with known reference gas (e.g., 2000 ppm).

### Automatic Baseline Correction (ABC)
- **Default**: Enabled
- **Logic**: Assumes sensor sees 400 ppm at least once every 24 hours
- **Best for**: Indoor monitoring with regular ventilation
- **Disable for**: Enclosed spaces, controlled environments

## Troubleshooting

### Sensor Not Responding
- Check wiring (TX/RX not swapped?)
- Verify 5V power supply
- Wait 3 minutes for warm-up
- Check UART baud rate (9600)

### Inaccurate Readings
- Warm-up sensor for 24+ hours for best accuracy
- Perform zero calibration in fresh air
- Ensure ABC is enabled for indoor use
- Check for sensor aging (3-5 year lifespan)

### High Power Consumption
- Normal during warm-up (first 3 minutes)
- Reduce publish frequency
- Use deep sleep mode (requires code modification)

### MQTT Connection Fails
- Verify broker IP address
- Check WiFi credentials
- Ensure firewall allows port 1883

## Sensor Maintenance

- **Warm-up**: Wait 3 minutes after power-on
- **Burn-in**: Run continuously for 24 hours for best accuracy
- **Calibration**: Zero calibrate every 6 months in fresh air
- **Lifespan**: 3-5 years typical
- **Storage**: Keep dry, avoid extreme temperatures

## Integration with Imperium

### Register Device
```bash
# Add to devices.yaml
echo "esp32-mhz19-1:
  type: co2_sensor
  model: MH-Z19B
  capabilities:
    - co2_monitoring
    - temperature
    - calibration
  mqtt_topics:
    telemetry: imperium/devices/esp32-mhz19-1/telemetry
    control: imperium/devices/esp32-mhz19-1/control
" >> /home/imperium/Imperium/config/devices.yaml
```

### Example Intents
```
"Monitor CO2 levels for esp32-mhz19-1"
"Set publish interval to 10 seconds for esp32-mhz19-1"
"Calibrate esp32-mhz19-1 to zero point"
"Alert if CO2 exceeds 1000 ppm"
```

## Safety & Health Information

### CO2 Concentration Effects
- **< 400 ppm**: Outdoor fresh air
- **400-1000 ppm**: Typical indoor levels (good)
- **1000-2000 ppm**: Drowsiness, poor air quality
- **2000-5000 ppm**: Headaches, reduced concentration
- **> 5000 ppm**: Serious health risks

### Recommendations
- Ventilate when CO2 > 1000 ppm
- Use for IAQ (Indoor Air Quality) monitoring
- Not certified for life safety applications

## References

- [MH-Z19B Datasheet](https://www.winsen-sensor.com/d/files/MH-Z19B.pdf)
- [ESP32 Documentation](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/)
- [UART Communication Guide](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/peripherals/uart.html)
