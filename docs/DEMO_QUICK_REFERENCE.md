# Imperium Demo - Quick Reference Card

## Launch Demo
```bash
cd /home/imperium/Imperium
python3 scripts/demo_menu.py
# or use alias: demo
```

## Main Menu Structure

### Authentication (1-2)
- **1** - Login (admin/admin)
- **2** - Check API Health

### Intent Management (3-6)
- **3** - Submit Intent (Examples) - 38 preset intents across all node types
- **4** - Submit Custom Intent - Free-form natural language
- **5** - List All Intents
- **6** - List Policies

### System Status (7-9)
- **7** - Docker Containers (13 running)
- **8** - Network (TC) Status
- **9** - System Overview

### Monitoring (10-11)
- **10** - Prometheus Menu
- **11** - Grafana Menu

### IoT Nodes (12-13)
- **12** - IoT Node Menu ⭐ **ESP32 integrated here**
- **13** - Live IoT Status (auto-refresh)

### Live Dashboards (14-16)
- **14** - Live System Metrics
- **15** - Live Network Stats
- **16** - Full Dashboard

### Demo (17)
- **17** - Run Full Demo (Automated sequence)

### Exit
- **q** - Quit

---

## IoT Node Menu (Option 12)

### Information
- **1** - Show Node Details
- **2** - List Nodes (Simulated + ESP32) ⭐
- **3** - View Logs

### Control
- **4** - Send MQTT Control Message ⭐ ESP32 templates
- **5** - View MQTT Messages
- **6** - Check Prometheus Metrics

### ESP32 Hardware
- **e** - ESP32 Audio Node Menu ⭐ **NEW**

### Monitoring
- **7** - Live Node Status

### Navigation
- **b** - Back to main menu

---

## ESP32 Audio Node Menu (Option 12 → e)

### Quick Actions (1-4)
- **1** - View Current Metrics (sample rate, gain, interval, QoS, frames, RMS)
- **2** - Test Sample Rate (8k/16k/44.1k/48k Hz)
- **3** - Test Audio Gain (0.1-10.0x)
- **4** - Test Publish Interval (1-60s)

### Intent Control (5-6)
- **5** - Submit ESP32 Intent (natural language)
- **6** - View Intent Examples (15 categorized)

### Monitoring (7-9)
- **7** - Live Metrics (auto-refresh 2s)
- **8** - Prometheus Queries (6 pre-configured)
- **9** - Open Grafana Dashboard

### Advanced (a, r)
- **a** - Send Raw MQTT Command (5 templates + custom)
- **r** - Reset to Defaults (factory reset)

### Navigation
- **b** - Back to IoT Node Menu

---

## Sample Intents (All 38 Verified ✓)

### Simulated Nodes (node-1 to node-10)
```
QoS:      set qos level 2 for node-1
          reliable delivery for node-3
Control:  enable device node-5
          disable node-2
          reset device node-7
Network:  prioritize node-1
          set high priority for node-10
```

### ESP32 CO₂ Sensor (esp32-mhz19-1)
```
Sampling: set sampling interval for esp32-mhz19-1 to 30 seconds
          read co2 every 10 seconds for esp32-mhz19-1
QoS:      set qos level 2 for esp32-mhz19-1
Control:  reset esp32-mhz19-1
Network:  limit bandwidth to 1mbit for esp32-mhz19-1
          add latency of 50ms for esp32-mhz19-1
          set high priority for esp32-mhz19-1
```

### ESP32 Audio Node (esp32-audio-1)
```
Sample Rate:  set sample rate to 48000 hz for esp32-audio-1
              16 khz sampling for esp32-audio-1

Audio Gain:   set audio gain to 3.5 for esp32-audio-1
              amplify audio by 2x for esp32-audio-1

Telemetry:    send data every 5 seconds for esp32-audio-1

QoS:          qos level 1 for esp32-audio-1

Control:      disable esp32-audio-1
              enable esp32-audio-1

Network:      limit bandwidth to 500kbit for esp32-audio-1
```

### ESP32-CAM (esp32-cam-1)
```
Resolution:   set resolution to VGA for esp32-cam-1
              change to HD resolution for esp32-cam-1
              set resolution to UXGA for esp32-cam-1

Quality:      set camera quality to 10 for esp32-cam-1
              set camera quality to 5 for esp32-cam-1

Brightness:   set camera brightness to 1 for esp32-cam-1

Framerate:    set camera fps to 5 for esp32-cam-1
              capture every 3 seconds for esp32-cam-1

Camera Ctrl:  disable camera for esp32-cam-1
              enable camera for esp32-cam-1

QoS:          set qos level 2 for esp32-cam-1

Network (TC): limit bandwidth to 2mbit for esp32-cam-1
              add latency of 100ms for esp32-cam-1
              set high priority for esp32-cam-1
              minimize latency for esp32-cam-1
```

---

## Quick Demo Scenarios

### 1. Basic Intent Flow (30 seconds)
```
1. Main Menu → 3 (Submit Intent Examples)
2. Select: 1 (prioritize node-1)
3. View result, press Enter
4. Main Menu → 5 (List All Intents)
5. See intent in database
```

### 2. ESP32 Control (60 seconds)
```
1. Main Menu → 12 (IoT Node Menu)
2. Select: e (ESP32 Menu)
3. Select: 1 (View Metrics) - baseline
4. Select: 3 (Test Audio Gain)
5. Enter: 3.0
6. Wait 5s, see updated metrics
7. Select: 1 again - verify change
```

### 3. Custom Intent (45 seconds)
```
1. Main Menu → 4 (Submit Custom Intent)
2. Type: "set sample rate to 48000 hz for esp32-audio-1"
3. Press Enter, wait for confirmation
4. Main Menu → 12 → e → 1
5. Verify: Sample Rate = 48000 Hz
```

### 4. Live Monitoring (ongoing)
```
1. Main Menu → 12 → e
2. Select: 7 (Live Metrics)
3. Watch auto-refresh every 2s
4. Press Ctrl+C to stop
```

### 5. Full Automated Demo (3 minutes)
```
1. Main Menu → 17 (Run Full Demo)
2. System automatically walks through:
   - Health check & authentication
   - Simulated nodes: QoS, device enable, priority
   - CO₂ sensor: sampling, QoS, bandwidth, latency
   - Audio node: sample rate, gain, publish interval
   - ESP32-CAM: resolution, quality, brightness, framerate, TC rules
   - Network enforcement status summary
3. Press Enter between steps
```

---

## Navigation Tips

- **Main Menu**: Always accessible with 'q' from submenus
- **Back**: Use 'b' to go back one level
- **Live Views**: Press Ctrl+C to exit auto-refresh
- **ESP32 Offline**: Menu shows "OFFLINE", all options still accessible
- **Timeout**: Live views timeout after 5 minutes of inactivity

---

## System Health Check

### Quick Verification
```bash
# All-in-one test
bash /home/imperium/Imperium/final_demo_test.sh

# Individual checks
curl http://localhost:5000/health           # API
curl http://10.218.189.218:8080/metrics     # ESP32
docker ps | grep -c imperium                # Containers
sudo systemctl status imperium              # Main service
```

### Expected Results
- API: "status": "healthy"
- ESP32: Shows Prometheus metrics (if online)
- Containers: 13 running
- Service: Active (running)

---

## Troubleshooting

### Demo Menu Won't Load
```bash
# Check Python environment
cd /home/imperium/Imperium
source venv/bin/activate
python3 scripts/demo_menu.py
```

### ESP32 Shows OFFLINE
```bash
# Check ESP32 network
ping 10.218.189.218
curl http://10.218.189.218:8080/metrics

# ESP32 offline is OK - demo works without it
# Menu handles this gracefully
```

### Intents Not Enforcing
```bash
# Restart main service
sudo systemctl restart imperium

# Check MQTT broker
docker logs imperium-mqtt-1 --tail 50

# Verify device enforcer loaded
journalctl -u imperium -n 50 | grep enforcer
```

### API Errors
```bash
# Check API logs
journalctl -u imperium -f

# Verify database
ls -lh /home/imperium/Imperium/data/imperium.db

# Reset if needed
sudo systemctl restart imperium
```

---

## API Access (Alternative to Menu)

### Login
```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'
# Returns: {"token": "eyJ..."}
```

### Submit Intent
```bash
TOKEN="your_token_here"
curl -X POST http://localhost:5000/api/v1/intents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description":"set audio gain to 2.5 for esp32-audio-1"}'
```

### List Intents
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/v1/intents
```

---

## Monitoring URLs

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **API**: http://localhost:5000/health
- **ESP32**: http://10.218.189.218:8080/metrics

---

## Demo Best Practices

1. **Start Fresh**: Login first (Option 1 or automatic on intent submit)
2. **Show Variety**: Mix simulated nodes and ESP32 intents
3. **Use Live Views**: Options 7, 13, 14 for visual impact
4. **Verify Changes**: After intent, check metrics (Option 12→e→1)
5. **Grafana Impact**: Open dashboard while submitting intents
6. **Natural Language**: Emphasize free-form intent submission
7. **Error Handling**: Show ESP32 offline handling (graceful)

---

## Performance Expectations

- Intent parsing: <100ms
- Policy generation: <200ms
- MQTT enforcement: 200-500ms
- Total (intent → ESP32 update): <1 second
- Menu navigation: Instant
- Live refresh rate: 2 seconds

---

**Last Updated**: 2026-02-26
**Demo Version**: 4.0 (All Nodes, 38 Verified Intents)
**Status**: Production Ready ✅
