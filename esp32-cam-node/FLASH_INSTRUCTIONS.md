# ESP32-CAM Flash Instructions

## ✅ Build Complete!

Firmware successfully compiled: `esp32-cam-node.bin` (1.04MB)
Flash size: 4MB
Partition: 3MB app space (66% free)

## Hardware Wiring

### Programming Mode (FTDI USB-to-Serial)

| ESP32-CAM | FTDI Adapter |
|-----------|--------------|
| 5V        | VCC (5V)     |
| GND       | GND          |
| U0R       | TX           |
| U0T       | RX           |
| GPIO0     | GND (for flashing) |

**⚠️ IMPORTANT:**
- Use 5V power (ESP32-CAM needs ~500mA)
- Connect GPIO0 to GND BEFORE powering on (enters bootloader mode)
- Remove GPIO0 jumper after flashing
- Press RESET button after flash to run firmware

## Flash Commands

### 1. Connect Hardware
```bash
# Check serial port
ls -la /dev/ttyUSB*

# Expected: /dev/ttyUSB1 (ESP32-CAM)
# ESP32 audio is on /dev/ttyUSB0
```

### 2. Flash Firmware
```bash
cd /home/imperium/Imperium/esp32-cam-node
source setup_esp.sh
idf.py -p /dev/ttyUSB1 flash
```

### 3. Monitor Serial Output
```bash
# Remove GPIO0 jumper, press RESET button
idf.py -p /dev/ttyUSB1 monitor

# Exit monitor: Ctrl+]
```

### 4. Flash + Monitor (Combined)
```bash
idf.py -p /dev/ttyUSB1 flash monitor
```

## Troubleshooting

### Issue: "serial.serialutil.SerialException: Cannot configure port"
**Solution:** Make sure GPIO0 is connected to GND before powering on

### Issue: "Wrong boot mode detected (0x13)! The chip needs to be in download mode"
**Solution:** GPIO0 must be LOW during boot. Power cycle with GPIO0→GND connected.

### Issue: "Timed out waiting for packet header"
**Solution:**
1. Disconnect power
2. Connect GPIO0 to GND
3. Reconnect power
4. Run flash command immediately

### Issue: Camera not working after flash
**Solution:**
1. Remove GPIO0 jumper
2. Press RESET button
3. Check serial monitor for WiFi connection
4. Verify MQTT broker accessible: `ping 10.218.189.192`

## Post-Flash Verification

### 1. Check Serial Output
```
I (xxx) ESP32-CAM: WiFi connected
I (xxx) ESP32-CAM: IP address: 192.168.x.x
I (xxx) ESP32-CAM: MQTT connected
I (xxx) ESP32-CAM: Camera initialized (SVGA 800x600)
I (xxx) ESP32-CAM: HTTP server started on port 8080
```

### 2. Check Metrics Endpoint
```bash
curl http://<esp32-cam-ip>:8080/metrics
# Should show Prometheus metrics
```

### 3. Check MQTT Publishing
```bash
mosquitto_sub -h 10.218.189.192 -t iot/esp32-cam-1/# -v
# Should see telemetry and image data
```

## Features

**Firmware Version:** 1.0.0
**Device ID:** esp32-cam-1
**Hardware:** AI-Thinker ESP32-CAM, OV2640 Camera

**Capabilities:**
- WiFi: Galaxy A56 5G A76A
- MQTT Broker: 10.218.189.192:1883
- Default Resolution: SVGA (800x600)
- JPEG Quality: 10 (high quality)
- Frame Rate: Configurable (default: every 5s)
- HTTP Metrics: Port 8080

**Control Topics:**
- `iot/esp32-cam-1/control` - Change resolution, quality, brightness, framerate
- `iot/esp32-cam-1/telemetry` - Device metrics (10s interval)
- `iot/esp32-cam-1/images` - JPEG frames
- `iot/esp32-cam-1/status` - Online/offline

**Resolutions Supported:**
- QVGA: 320x240
- VGA: 640x480
- SVGA: 800x600
- XGA: 1024x768
- HD: 1280x720
- SXGA: 1280x1024
- UXGA: 1600x1200

**Quality Range:** 0-63 (0=best, 63=worst)
**Brightness Range:** -2 to +2
**Capture Interval:** 100ms to 60s

---

**Last Updated:** 2026-02-10
**ESP-IDF Version:** v5.1.2
