#!/bin/bash
# ESP32 MH-Z19 Node Setup Script

set -e

echo "═══════════════════════════════════════════════════════"
echo "  ESP32 MH-Z19 CO2 Sensor Node - Setup"
echo "═══════════════════════════════════════════════════════"

# Check if ESP-IDF is installed
if [ -z "$IDF_PATH" ]; then
    echo "⚠️  ESP-IDF not found. Please install ESP-IDF first:"
    echo "   https://docs.espressif.com/projects/esp-idf/en/latest/esp32/get-started/"
    exit 1
fi

echo "✓ ESP-IDF found: $IDF_PATH"

# Configuration
read -p "Enter WiFi SSID [YourWiFiSSID]: " WIFI_SSID
WIFI_SSID=${WIFI_SSID:-YourWiFiSSID}

read -p "Enter WiFi Password [YourWiFiPassword]: " WIFI_PASSWORD
WIFI_PASSWORD=${WIFI_PASSWORD:-YourWiFiPassword}

read -p "Enter MQTT Broker IP [192.168.1.100]: " MQTT_BROKER
MQTT_BROKER=${MQTT_BROKER:-192.168.1.100}

read -p "Enter Device ID [esp32-mhz19-1]: " DEVICE_ID
DEVICE_ID=${DEVICE_ID:-esp32-mhz19-1}

# Update config.h
echo ""
echo "Updating configuration..."
sed -i "s/YourWiFiSSID/$WIFI_SSID/g" main/config.h
sed -i "s/YourWiFiPassword/$WIFI_PASSWORD/g" main/config.h
sed -i "s/192\.168\.1\.100/$MQTT_BROKER/g" main/config.h
sed -i "s/esp32-mhz19-1/$DEVICE_ID/g" main/config.h

echo "✓ Configuration updated"
echo ""
echo "Configuration Summary:"
echo "  WiFi SSID: $WIFI_SSID"
echo "  MQTT Broker: mqtt://$MQTT_BROKER"
echo "  Device ID: $DEVICE_ID"
echo ""
echo "Next steps:"
echo "  1. idf.py build          - Build firmware"
echo "  2. idf.py -p PORT flash  - Flash to ESP32"
echo "  3. idf.py -p PORT monitor - Monitor output"
echo ""
echo "Wiring:"
echo "  MH-Z19 VCC → ESP32 5V (VIN)"
echo "  MH-Z19 GND → ESP32 GND"
echo "  MH-Z19 TX  → ESP32 GPIO16 (RX2)"
echo "  MH-Z19 RX  → ESP32 GPIO17 (TX2)"
echo ""
echo "═══════════════════════════════════════════════════════"
