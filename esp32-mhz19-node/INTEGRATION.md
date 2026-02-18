# MH-Z19 CO2 Sensor - Imperium Integration Guide

## Overview

The ESP32 MH-Z19 node is fully integrated with the Imperium Intent-Based Networking system, allowing for automated CO2 monitoring and air quality management through natural language intents.

## Device Registration

The device is pre-registered in `config/devices.yaml`:

```yaml
esp32-mhz19-1:
  type: co2_sensor
  model: MH-Z19B
  capabilities:
    - mqtt
    - co2_monitoring
    - temperature
    - calibration
    - prometheus_metrics
  mqtt_topics:
    telemetry: "imperium/devices/esp32-mhz19-1/telemetry"
    control: "imperium/devices/esp32-mhz19-1/control"
```

## Supported Intents

### 1. Set Publishing Interval
**Intent:** `"Set publish interval to 10 seconds for esp32-mhz19-1"`

**Generated Policy:**
```json
{
  "command": "SET_PUBLISH_INTERVAL",
  "interval_ms": 10000
}
```

### 2. Calibrate Sensor
**Intent:** `"Calibrate esp32-mhz19-1 to zero point"`

**Generated Policy:**
```json
{
  "command": "CALIBRATE_ZERO"
}
```

**Note:** Place sensor in fresh outdoor air for 20+ minutes before calibration.

### 3. Set Detection Range
**Intent:** `"Set detection range to 10000 ppm for esp32-mhz19-1"`

**Generated Policy:**
```json
{
  "command": "SET_DETECTION_RANGE",
  "range_ppm": 10000
}
```

**Valid ranges:** 2000, 5000, 10000 ppm

### 4. Enable/Disable ABC
**Intent:** `"Enable automatic baseline correction for esp32-mhz19-1"`

**Generated Policy:**
```json
{
  "command": "SET_ABC",
  "enabled": true
}
```

### 5. Get Sensor Info
**Intent:** `"Get sensor information for esp32-mhz19-1"`

**Generated Policy:**
```json
{
  "command": "GET_INFO"
}
```

## Intent Parser Integration

Add CO2 sensor patterns to `src/intent_manager/parser.py`:

```python
'co2_monitoring': [
    (r'(?:monitor|track)\s+co2\s+(?:for\s+)?(\S+)', 'device_id'),
    (r'(?:set\s+)?(?:co2\s+)?detection\s+range\s+(?:to\s+)?(\d+)', 'range_ppm'),
],
'calibration': [
    (r'calibrate\s+(\S+)\s+(?:to\s+)?(?:zero|400\s*ppm)?', 'device_id'),
    (r'(?:zero|baseline)\s+calibrat(?:e|ion)\s+(?:for\s+)?(\S+)', 'device_id'),
],
```

## Policy Engine Integration

Add CO2 policy generation to `src/policy_engine/engine.py`:

```python
elif intent_type == 'co2_monitoring':
    policies.extend(self._generate_co2_policies(parameters))

def _generate_co2_policies(self, parameters):
    """Generate CO2 monitoring policies"""
    device_id = parameters.get('target_device', 'esp32-mhz19-1')
    
    if 'range_ppm' in parameters:
        range_val = int(parameters['range_ppm'][0])
        return [Policy(
            policy_id=self._get_next_policy_id(),
            policy_type='co2_monitoring',
            target=device_id,
            priority=8,
            parameters={
                'command': 'SET_DETECTION_RANGE',
                'range_ppm': range_val
            }
        )]
```

## Monitoring with Prometheus

### Metrics Exporter
Create `/home/imperium/Imperium/monitoring/prometheus/mhz19_exporter.py`:

```python
#!/usr/bin/env python3
"""MH-Z19 Prometheus Exporter"""

import paho.mqtt.client as mqtt
import json
from prometheus_client import start_http_server, Gauge
import time

# Metrics
co2_ppm = Gauge('mhz19_co2_ppm', 'CO2 concentration', ['device_id'])
temperature = Gauge('mhz19_temperature_celsius', 'Temperature', ['device_id'])
rssi = Gauge('mhz19_wifi_rssi_dbm', 'WiFi signal strength', ['device_id'])

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload)
        device_id = data['device_id']
        
        co2_ppm.labels(device_id=device_id).set(data['co2_ppm'])
        temperature.labels(device_id=device_id).set(data['temperature'])
        rssi.labels(device_id=device_id).set(data['rssi'])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    client = mqtt.Client()
    client.on_message = on_message
    client.connect("localhost", 1883)
    client.subscribe("imperium/devices/esp32-mhz19-+/telemetry")
    
    start_http_server(9103)  # Prometheus scrape port
    print("MH-Z19 exporter started on :9103")
    
    client.loop_forever()
```

### Prometheus Configuration
Add to `monitoring/prometheus/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'mhz19'
    static_configs:
      - targets: ['localhost:9103']
    scrape_interval: 5s
```

### Grafana Dashboard
Create dashboard with:
- **CO2 Level Panel**: Time series graph
- **Temperature Panel**: Gauge
- **Air Quality Status**: Stat panel with thresholds
  - Green: < 800 ppm
  - Yellow: 800-1000 ppm
  - Orange: 1000-2000 ppm
  - Red: > 2000 ppm

## Alert Rules

### High CO2 Alert
Add to Prometheus `alert.rules.yml`:

```yaml
groups:
  - name: air_quality
    interval: 30s
    rules:
      - alert: HighCO2Level
        expr: mhz19_co2_ppm > 1000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CO2 detected: {{ $value }} ppm"
          description: "Ventilation recommended"
      
      - alert: CriticalCO2Level
        expr: mhz19_co2_ppm > 2000
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Critical CO2: {{ $value }} ppm"
          description: "Immediate action required"
```

## Automated Intent Examples

### Monitor Air Quality
```bash
curl -X POST http://localhost:5000/api/v1/intents \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"description":"Monitor CO2 levels every 5 seconds for esp32-mhz19-1"}'
```

### Daily Calibration
```bash
# Cron job for daily calibration at 6 AM (outdoor air)
0 6 * * * curl -X POST http://localhost:5000/api/v1/intents \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"description":"Calibrate esp32-mhz19-1 to zero point"}'
```

### Alert-Based Ventilation
```python
# In feedback/engine.py
if co2_ppm > 1000:
    intent_manager.submit_intent(
        "Increase ventilation priority for zone-office"
    )
```

## Testing

### 1. Submit Test Intent
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

### 2. Verify MQTT Command
```bash
mosquitto_sub -h localhost -v -t "imperium/devices/esp32-mhz19-1/control"
```

### 3. Monitor Telemetry
```bash
mosquitto_sub -h localhost -t "imperium/devices/esp32-mhz19-1/telemetry" | \
    while read line; do
        echo "[$(date +%T)] $line" | jq '.co2_ppm, .temperature'
    done
```

## Safety Recommendations

### CO2 Level Actions
| CO2 (ppm) | Status | Action |
|-----------|--------|--------|
| < 400 | Outdoor | Normal |
| 400-800 | Good | No action |
| 800-1000 | Acceptable | Monitor |
| 1000-1500 | Poor | Increase ventilation |
| 1500-2000 | Very Poor | Open windows |
| > 2000 | Dangerous | Evacuate space |

### Automated Responses
Configure Imperium to:
1. **1000 ppm**: Send notification, log event
2. **1500 ppm**: Trigger HVAC system increase
3. **2000 ppm**: Send critical alert, flash lights

## Full Integration Example

```python
# In src/main.py - add CO2 monitoring loop

from feedback.engine import FeedbackEngine
import paho.mqtt.client as mqtt

feedback = FeedbackEngine()

def on_co2_message(client, userdata, msg):
    data = json.loads(msg.payload)
    co2_ppm = data['co2_ppm']
    device_id = data['device_id']
    
    # Check thresholds
    if co2_ppm > 2000:
        intent_manager.submit_intent(
            f"CRITICAL: High CO2 in {device_id} - immediate ventilation"
        )
    elif co2_ppm > 1000:
        intent_manager.submit_intent(
            f"Increase ventilation for {device_id}"
        )
    
    # Store in database
    feedback.record_metric(device_id, 'co2_ppm', co2_ppm)

mqtt_client.subscribe("imperium/devices/esp32-mhz19-+/telemetry")
mqtt_client.on_message = on_co2_message
```

## Next Steps

1. **Build and flash** firmware to ESP32
2. **Verify connectivity** (WiFi and MQTT)
3. **Test intents** through API
4. **Configure alerts** in Prometheus
5. **Create dashboard** in Grafana
6. **Set up automation** rules

See [README.md](README.md) and [QUICKSTART.md](QUICKSTART.md) for hardware setup.
