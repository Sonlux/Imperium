#!/bin/bash
# ESP-IDF Environment Setup Script
# Source this file before building: source setup_esp.sh

export IDF_PATH=~/esp/esp-idf

# Load ESP-IDF environment
if [ -f "$IDF_PATH/export.sh" ]; then
    . $IDF_PATH/export.sh
    echo "✅ ESP-IDF environment loaded"
else
    echo "❌ ESP-IDF not found at $IDF_PATH"
    echo "Run: cd ~/esp && git clone --depth 1 --branch v5.1.2 https://github.com/espressif/esp-idf.git"
    exit 1
fi

# Show quick commands
echo ""
echo "Quick Commands:"
echo "  idf.py build              - Build firmware"
echo "  idf.py -p /dev/ttyUSB0 flash - Flash to ESP32"
echo "  idf.py monitor            - View serial output"
echo "  idf.py flash monitor      - Flash and monitor"
echo ""
