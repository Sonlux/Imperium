# ESP32 WiFi/MQTT Connection Troubleshooting

## Current Status
- ✅ Firmware flashed successfully
- ✅ MQTT broker running (10.218.189.192:1883)
- ✅ WiFi connecting intermittently
- ❌ MQTT connection failing ("Host is unreachable")

## Root Cause: AP Isolation
Your mobile hotspot "Galaxy A56 5G A76A" likely has **AP Isolation** enabled, preventing ESP32 from reaching Raspberry Pi.

## Solutions (Pick One)

### Option 1: Disable AP Isolation (Recommended)
1. Go to **Settings → Connections → Mobile Hotspot and Tethering**
2. Tap **Mobile Hotspot → Configure**
3. Look for **"AP Isolation"** or **"Client Isolation"** setting
4. **Disable** it
5. Restart hotspot

### Option 2: Use Raspberry Pi as WiFi Access Point
```bash
# Install hostapd
sudo apt install hostapd dnsmasq

# Configure wlan0 as AP (creates new network)
sudo nmcli dev wifi hotspot ssid Imperium-IBN password ImperiumESP32
```
Then update ESP32 config.h:
```cpp
#define WIFI_SSID "Imperium-IBN"
#define WIFI_PASSWORD "ImperiumESP32"
#define MQTT_BROKER_URI "mqtt://10.42.0.1:1883"  // Pi's AP IP
```

### Option 3: Use USB Tethering
1. Connect phone to Raspberry Pi via USB
2. Enable **USB Tethering** on phone
3. Check new IP: `ip addr show usb0`
4. Update ESP32 config with new IP

### Option 4: Use Ethernet (If Available)
1. Connect Raspberry Pi to router via Ethernet
2. Get eth0 IP: `ip addr show eth0`
3. Connect ESP32 to router's WiFi
4. Update ESP32 config with Pi's eth0 IP

## Verification Steps
After applying a solution:

1. **Test connectivity from ESP32's perspective:**
   ```bash
   # On Raspberry Pi, simulate ESP32
   ping -I wlan0 10.218.189.192  # Should work
   ```

2. **Monitor serial output:**
   ```bash
   idf.py monitor
   ```
   Look for: `I (xxxx) MQTT: MQTT connected`

3. **Check MQTT broker logs:**
   ```bash
   docker logs -f imperium-mqtt
   ```
   Should see: `New client connected from 10.218.189.x`

## Quick Test Command
```bash
# Rebuild and flash with corrected MQTT port
cd ~/Imperium/esp32-audio-node
. ~/esp/esp-idf/export.sh
idf.py build flash monitor
```

## Current Configuration
- WiFi SSID: `Galaxy A56 5G A76A`
- WiFi Password: `12345678`
- MQTT Broker: `mqtt://10.218.189.192:1883` ✅ (fixed)
- Device ID: `esp32-audio-1`

