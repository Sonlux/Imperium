# ESP32 Audio Node - Imperium IBN Integration

Real-time audio streaming node with I2S microphone for the Imperium Intent-Based Networking framework.

## Hardware Requirements

- **ESP32 Board**: ESP32-DevKitC, ESP32-WROOM-32, or similar
- **I2S Microphone**: INMP441, ICS-43434, or MAX98357A
- **Power**: USB (5V) or LiPo battery (3.7V + regulator)

## Wiring Diagram

```
ESP32 Pin    →    I2S Microphone
GPIO25       →    SCK  (Serial Clock)
GPIO33       →    WS   (Word Select / LRCK)
GPIO32       →    SD   (Serial Data)
3.3V         →    VDD
GND          →    GND
```

**Note**: L/R pin on microphone should be connected to GND for left channel or VDD for right channel.

## Software Requirements

### ESP-IDF Setup

```bash
# Install ESP-IDF v5.x
mkdir -p ~/esp
cd ~/esp
git clone --recursive https://github.com/espressif/esp-idf.git
cd esp-idf
git checkout v5.1.2
./install.sh esp32
source export.sh
```

### Project Configuration

Edit `main/config.h` with your settings:

```cpp
#define WIFI_SSID                "YourWiFiSSID"
#define WIFI_PASSWORD            "YourPassword"
#define MQTT_BROKER_URI          "mqtt://192.168.1.100:1883"  // Raspberry Pi IP
#define DEVICE_ID                "esp32-audio-1"
```

## Building & Flashing

```bash
cd esp32-audio-node

# Configure project (optional - adjust I2S pins, sample rate)
idf.py menuconfig

# Build firmware
idf.py build

# Flash to ESP32
idf.py -p /dev/ttyUSB0 flash

# Monitor serial output
idf.py -p /dev/ttyUSB0 monitor
```

**Windows**: Replace `/dev/ttyUSB0` with `COM3` (check Device Manager)

## Features

### Audio Capture
- **Sample Rate**: 16 kHz (configurable: 8k, 16k, 44.1k, 48k)
- **Bit Depth**: 16-bit PCM
- **Channels**: Mono
- **Latency**: <100ms (capture → MQTT publish)
- **Buffer Size**: 30ms frames (480 samples @ 16kHz)

### MQTT Topics

```
iot/esp32-audio-1/audio       → Audio data (PCM chunks)
iot/esp32-audio-1/telemetry   → Device metrics (every 10s)
iot/esp32-audio-1/control     → Policy commands (subscribed)
iot/esp32-audio-1/status      → Heartbeat (every 10s)
iot/esp32-audio-1/metadata    → Audio format info (retained)
```

### Policy Commands

Submit via MQTT to `iot/esp32-audio-1/control`:

**Set QoS Level**:
```json
{"command": "SET_QOS", "qos": 1}
```

**Change Sample Rate**:
```json
{"command": "SET_SAMPLE_RATE", "sample_rate": 8000}
```

**Enable/Disable Device**:
```json
{"command": "ENABLE"}
{"command": "DISABLE"}
```

**Reset to Defaults**:
```json
{"command": "RESET"}
```

### Prometheus Metrics

Access metrics at `http://<esp32-ip>:8080/metrics`:

```
audio_frames_captured_total          # Total frames captured
audio_buffer_overruns_total          # Buffer overflow count
mqtt_messages_published_total        # MQTT publish count
mqtt_publish_errors_total            # MQTT errors
audio_rms_level_db                   # Current audio level (dB)
audio_peak_amplitude                 # Peak amplitude (0-1)
mqtt_qos_level                       # Current QoS setting
audio_sample_rate_hz                 # Current sample rate
```

## Testing

### 1. Verify Audio Capture

```bash
# Monitor serial output
idf.py monitor

# Expected logs:
# I (5432) I2S_AUDIO: I2S initialized successfully
# I (5678) I2S_AUDIO: Audio capture started
# I (6000) MQTT: MQTT connected
```

### 2. Subscribe to Audio Stream

```bash
# On Raspberry Pi
mosquitto_sub -h localhost -t 'iot/esp32-audio-1/#' -v

# Expected output:
# iot/esp32-audio-1/status {"device_id":"esp32-audio-1","status":"online"}
# iot/esp32-audio-1/metadata {"sample_rate":16000,"channels":1}
# iot/esp32-audio-1/audio <binary data>
```

### 3. Send Test Control Command

```bash
# Change QoS to 0 (best effort)
mosquitto_pub -h localhost -t 'iot/esp32-audio-1/control' \
  -m '{"command":"SET_QOS","qos":0}'

# Monitor ESP32 serial - should see:
# I (12345) POLICY: Command: SET_QOS
# I (12346) POLICY: QoS set to 0
```

### 4. Check Prometheus Metrics

```bash
curl http://<esp32-ip>:8080/metrics

# Or add to Prometheus:
# Edit monitoring/prometheus/prometheus.yml
scrape_configs:
  - job_name: 'esp32-audio'
    static_configs:
      - targets: ['<esp32-ip>:8080']
```

## Imperium Integration

### 1. Register Device

Add to `/home/imperium/Imperium/config/devices.yaml`:

```yaml
esp32-audio-1:
  type: audio_sensor
  description: "ESP32 I2S microphone - ambient monitoring"
  capabilities:
    - mqtt
    - audio_stream
    - prometheus_metrics
  qos_profile: high_priority
  priority_level: 8
  default_sampling_rate: 16000
  mqtt_topics:
    data: "iot/esp32-audio-1/audio"
    control: "iot/esp32-audio-1/control"
    status: "iot/esp32-audio-1/status"
  network:
    max_bandwidth: "300kbps"
    target_bandwidth: "64kbps"
    min_latency: "50ms"
  location: "lab-area-1"
```

### 2. Restart Imperium

```bash
sudo systemctl restart imperium
```

### 3. Submit Intent

```bash
# Prioritize audio node
curl -X POST http://localhost:5000/intent \
  -H "Content-Type: application/json" \
  -d '{"intent": "prioritize esp32-audio-1 and limit latency to 50ms"}'

# Verify policy applied
sudo tc -s qdisc show dev eth0
```

## Troubleshooting

### No Audio Output
- **Check wiring**: Verify I2S pins match config.h
- **Check power**: Microphone needs 3.3V (not 5V!)
- **Check L/R pin**: Must be tied to GND or VDD
- **Monitor serial**: Look for "I2S read error" messages

### MQTT Not Connecting
- **Verify broker IP**: Ping Raspberry Pi from ESP32 network
- **Check firewall**: Port 1883 must be open
- **Test with mosquitto_pub**: Verify broker is running
- **Check WiFi credentials**: SSID/password in config.h

### High Buffer Overruns
- **Reduce sample rate**: Lower to 8kHz
- **Increase QoS**: Set to 0 for faster publishing
- **Check network**: WiFi signal strength, congestion
- **Optimize task priorities**: Increase TASK_PRIORITY_MQTT

### Low Audio Quality
- **Increase sample rate**: 44.1kHz for better quality
- **Check mic placement**: Away from ESP32 (electrical noise)
- **Add filtering**: Implement high-pass filter for DC offset
- **Calibrate gain**: Some mics need software gain adjustment

## Performance Benchmarks

| Configuration | Bandwidth | Latency | CPU % | Power (mA) |
|--------------|-----------|---------|-------|------------|
| 16kHz, QoS 1 | 256 Kbps  | 80ms    | 35%   | 180        |
| 8kHz, QoS 0  | 128 Kbps  | 50ms    | 20%   | 150        |
| 44.1kHz, QoS 2 | 705 Kbps | 120ms  | 60%   | 220        |

## Next Steps

1. **Audio Compression**: Implement Opus codec for 4:1 compression
2. **Voice Activity Detection**: Only send audio when speech detected
3. **OTA Updates**: Add remote firmware update capability
4. **TLS Security**: Enable MQTT over TLS (port 8883)
5. **Edge Processing**: Extract audio features (FFT, MFCC) on-device

## License

See project root LICENSE file.
