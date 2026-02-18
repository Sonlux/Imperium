# ESP32 Live Demo Integration - Summary

## Overview
Successfully integrated ESP32 audio node controls into the existing Imperium interactive demo menu (`scripts/demo_menu.py`). All ESP32 features are now accessible through the live demo interface without creating redundant sections.

## Integration Points

### 1. **Main Menu - Custom Intent Section (Option 4)**
**Location**: Main menu → Submit Custom Intent

**Enhancement**: Added ESP32-specific intent examples alongside existing simulated node examples.

**New Examples Shown**:
```
ESP32 Audio Node (esp32-audio-1):
  - set sample rate to 48000 hz for esp32-audio-1
  - set audio gain to 2.5 for esp32-audio-1
  - set telemetry rate to 5 seconds for esp32-audio-1
  - amplify audio by 3x for esp32-audio-1
  - report telemetry every 2 seconds for esp32-audio-1
```

**Path**: Main Menu → 4 (Submit Custom Intent)

---

### 2. **IoT Node Menu - Enhanced Title**
**Location**: Main Menu → 12 (IoT Node Menu)

**Change**: 
- Title changed from "IOT NODE SIMULATOR" to **"IOT NODE MANAGEMENT"**
- Subtitle now shows: "List Running Nodes **(Simulated + ESP32)**"

This reflects that the menu now manages both simulated Docker nodes and real ESP32 hardware.

---

### 3. **IoT Node Menu - New ESP32 Section**
**Location**: IoT Node Menu → Option 'e'

**New Section**:
```
  ESP32 Hardware Node:
    e. ESP32 Audio Node Menu
```

**Features**: Dedicated submenu for ESP32 controls with 12 options.

**Path**: Main Menu → 12 (IoT Node Menu) → e (ESP32 Audio Node Menu)

---

### 4. **ESP32 Dedicated Submenu**
**Location**: IoT Node Menu → e (ESP32 Audio Node Menu)

**Complete Menu Structure**:
```
╔══════════════════════════════════════════════════════════╗
║            ESP32 AUDIO NODE (Hardware)                   ║
╠══════════════════════════════════════════════════════════╣
  Status: ONLINE/OFFLINE
  Device: esp32-audio-1  |  IP: 10.218.189.218  |  Port: 8080

  Quick Actions:
    1. View Current Metrics        2. Test Sample Rate Change
    3. Test Audio Gain Change      4. Test Publish Interval
    
  Intent-Based Control:
    5. Submit ESP32 Intent         6. View ESP32 Intent Examples
    
  Monitoring:
    7. Live Metrics (auto-refresh) 8. Prometheus Queries
    9. Open Grafana Dashboard
    
  Advanced:
    a. Send Raw MQTT Command       r. Reset to Defaults
    
   b. Back to IoT Node Menu
╚══════════════════════════════════════════════════════════╝
```

**Functions Implemented**:

#### Quick Actions (1-4):
- **View Current Metrics**: Shows sample rate, audio gain, publish interval, QoS, frames captured, RMS level
- **Test Sample Rate**: Interactive sample rate change (8000/16000/44100/48000 Hz)
- **Test Audio Gain**: Interactive gain adjustment (0.1-10.0x)
- **Test Publish Interval**: Interactive telemetry rate change (1-60 seconds)

#### Intent-Based Control (5-6):
- **Submit ESP32 Intent**: Free-form natural language intent submission
- **View Intent Examples**: Categorized examples for:
  - Sample Rate Control (3 examples)
  - Audio Gain Control (3 examples)
  - Publish Interval Control (3 examples)
  - QoS Control (3 examples)
  - Device Control (3 examples)

#### Monitoring (7-9):
- **Live Metrics**: Auto-refreshing metrics display (2-second interval)
- **Prometheus Queries**: Direct Prometheus queries for 6 key metrics
- **Open Grafana Dashboard**: Opens ESP32-specific Grafana dashboard

#### Advanced (a, r):
- **Send Raw MQTT Command**: Direct MQTT control message with templates
- **Reset to Defaults**: One-click reset to factory settings

---

### 5. **Enhanced Node Listing**
**Location**: IoT Node Menu → 2 (List Running Nodes)

**Enhancement**: Now shows both simulated and hardware nodes in separate sections.

**Output Format**:
```
Simulated Nodes (Docker):
  [Docker container table]

Hardware Nodes:
  ● esp32-audio-1 - ONLINE (10.218.189.218:8080)
    OR
  ○ esp32-audio-1 - OFFLINE
```

**Status Detection**: Real-time HTTP health check to ESP32 metrics endpoint.

**Path**: Main Menu → 12 (IoT Node Menu) → 2 (List Running Nodes)

---

### 6. **Updated MQTT Control Examples**
**Location**: IoT Node Menu → 4 (Send Control Message)

**Enhancement**: Added ESP32-specific MQTT command examples.

**New Examples**:
```
ESP32 Audio Node Commands (for esp32-audio-1):
  • {"command":"SET_SAMPLE_RATE","sample_rate":48000}
  • {"command":"SET_AUDIO_GAIN","gain":2.5}
  • {"command":"SET_PUBLISH_INTERVAL","interval_ms":5000}
  • {"command":"SET_QOS","qos":2}
  • {"command":"RESET"}
```

**Path**: Main Menu → 12 (IoT Node Menu) → 4 (Send Control Message)

---

## User Workflows

### Quick Test Workflow
1. Launch demo: `python3 scripts/demo_menu.py` or `demo` (if aliases loaded)
2. Navigate: **12** (IoT Node Menu) → **e** (ESP32 Menu)
3. Check status: **1** (View Current Metrics)
4. Test feature: **2** (Sample Rate) / **3** (Audio Gain) / **4** (Publish Interval)
5. Verify: Metrics update in real-time

### Intent-Based Workflow
1. Main Menu → **4** (Submit Custom Intent)
2. Select ESP32 example or type custom intent
3. System automatically:
   - Parses intent
   - Generates policy
   - Sends MQTT command to ESP32
   - Verifies enforcement
4. Check result in ESP32 Menu → **1** (Metrics)

### Monitoring Workflow
1. ESP32 Menu → **7** (Live Metrics)
2. Watch real-time updates (auto-refresh every 2s)
3. Press Ctrl+C to stop
4. Alternative: **8** (Prometheus Queries) for historical data

### Advanced Workflow
1. ESP32 Menu → **a** (Send Raw MQTT Command)
2. Select command template (1-5) or enter custom JSON
3. Command sent directly to MQTT broker
4. Instant enforcement (no Intent Parser overhead)

---

## Key Features

### Real-Time Status Detection
- ESP32 online/offline status shown in menu header
- Color-coded: Green (online) / Red (offline)
- Automatic health check on every menu render

### Intent Integration
- All 5 ESP32 intent types supported:
  1. Sample Rate (8k/16k/44.1k/48k Hz)
  2. Audio Gain (0.1-10.0x)
  3. Publish Interval (1-60 seconds)
  4. QoS Level (0/1/2)
  5. Device Control (Enable/Disable/Reset)

### Validation
- Interactive tests auto-verify changes after 5-second delay
- Metrics display shows before/after values
- Failed commands show error messages

### Prometheus Integration
- 6 pre-configured queries:
  - Current Sample Rate
  - Current Audio Gain
  - Publish Interval
  - Frames Captured
  - Audio RMS Level
  - Buffer Overruns
- Results displayed with proper formatting

---

## Technical Implementation

### Files Modified
- **scripts/demo_menu.py**: ~450 lines added
  - New function: `esp32_menu()` - Main ESP32 submenu
  - New function: `show_esp32_metrics()` - Display current metrics
  - New function: `test_esp32_sample_rate()` - Interactive sample rate test
  - New function: `test_esp32_audio_gain()` - Interactive gain test
  - New function: `test_esp32_publish_interval()` - Interactive interval test
  - New function: `submit_esp32_intent()` - Custom intent submission
  - New function: `show_esp32_intent_examples()` - Example intent catalog
  - New function: `live_esp32_metrics()` - Auto-refresh monitoring
  - New function: `esp32_prometheus_queries()` - Prometheus integration
  - New function: `send_esp32_raw_command()` - Direct MQTT control
  - New function: `reset_esp32()` - Factory reset
  - Enhanced: Main menu custom intent examples
  - Enhanced: IoT node listing (simulated + hardware)
  - Enhanced: MQTT control examples

### Configuration
- **ESP32 IP**: `10.218.189.218` (hardcoded, can be env var)
- **ESP32 Metrics Port**: `8080`
- **Refresh Interval**: 2 seconds (shared with other live views)
- **MQTT Topic**: `iot/esp32-audio-1/control`

### Dependencies
- Existing: `requests`, `json`, `subprocess`, `os`, `sys`, `time`
- No new dependencies required

---

## Testing Results

### Menu Navigation
✅ Main menu renders correctly  
✅ IoT Node Menu shows "Simulated + ESP32" subtitle  
✅ ESP32 submenu accessible via option 'e'  
✅ All 12 ESP32 submenu options functional  

### Status Detection
✅ Online detection works (HTTP 200 from metrics endpoint)  
✅ Offline detection works (connection timeout)  
✅ Status updates on menu re-render  

### Intent Submission
✅ ESP32 examples shown in main menu custom intent  
✅ Intent submission works from ESP32 submenu  
✅ Intent examples catalog displays correctly  

### Metrics Display
✅ Current metrics parsed from Prometheus format  
✅ Sample rate, gain, interval, QoS, frames displayed  
✅ Formatting correct (Hz, x, seconds, etc.)  

### Interactive Tests
✅ Sample rate test: submit intent → wait → verify  
✅ Audio gain test: submit intent → wait → verify  
✅ Publish interval test: submit intent → wait → verify  

### Live Monitoring
✅ Auto-refresh works (2-second interval)  
✅ Ctrl+C gracefully exits  
✅ Timestamp displayed on each refresh  

### Prometheus Queries
✅ All 6 queries execute successfully  
✅ Values displayed with proper formatting  
✅ "No data" shown when metric unavailable  

### MQTT Commands
✅ Raw command templates provided  
✅ Interactive command builder works  
✅ Direct MQTT publish succeeds  

---

## Demo Showcase Value

### Before Integration
- ESP32 required separate scripts/commands
- No visibility in main demo interface
- Manual MQTT commands needed for testing
- Disconnected from Intent-Based Networking workflow

### After Integration
- **One-stop demo interface** for all IoT devices
- **Seamless IBN workflow**: Intent → Policy → Enforcement → Validation
- **Live monitoring** with auto-refresh
- **Interactive testing** with instant feedback
- **Hardware + simulated nodes** managed together

### Key Selling Points
1. **Natural Language Control**: "Set audio gain to 2.5" instead of JSON MQTT payloads
2. **Real-Time Feedback**: See changes within 5 seconds
3. **User-Friendly**: No command-line knowledge required
4. **Production-Ready**: Same interface for demos and actual deployments
5. **Comprehensive**: Metrics, intents, Prometheus, Grafana all integrated

---

## Future Enhancements (Optional)

- [ ] Auto-detect ESP32 IP via mDNS/Zeroconf
- [ ] Add ESP32 connection wizard for first-time setup
- [ ] Historical metrics graphs in terminal (using termgraph)
- [ ] Batch intent submission (apply multiple intents to ESP32)
- [ ] ESP32 firmware update via demo menu
- [ ] Audio playback preview (if audio samples stored)

---

## Usage Examples

### Example 1: Quick Health Check
```bash
$ python3 scripts/demo_menu.py
# Select: 12 (IoT Node Menu)
# Select: e (ESP32 Menu)
# Select: 1 (View Current Metrics)
# Output shows all 6 metrics with current values
```

### Example 2: Test Audio Gain
```bash
$ python3 scripts/demo_menu.py
# Select: 12 → e → 3 (Test Audio Gain)
# Enter: 5.0
# System submits intent: "Set audio gain to 5.0 for esp32-audio-1"
# Waits 5s, then shows updated metrics
```

### Example 3: Live Monitoring
```bash
$ python3 scripts/demo_menu.py
# Select: 12 → e → 7 (Live Metrics)
# Metrics auto-refresh every 2 seconds
# Press Ctrl+C to exit
```

### Example 4: Natural Language Intent
```bash
$ python3 scripts/demo_menu.py
# Select: 4 (Submit Custom Intent)
# Type: "amplify audio by 3x for esp32-audio-1"
# System handles: Parse → Policy → MQTT → Enforcement
# Check result: 12 → e → 1
```

---

**Integration Date**: 2026-02-08  
**Total Functions Added**: 11  
**Lines of Code Added**: ~450  
**Zero Breaking Changes**: All existing functionality preserved  
**ESP32 Firmware Required**: v1.0.0 (build 975968 bytes)
