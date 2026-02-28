#!/bin/bash
# Quick build and flash script for ESP32 MH-Z19 Node

set -e

PORT=${1:-/dev/ttyUSB0}

echo "═══════════════════════════════════════════════════════"
echo "  Building and Flashing ESP32 MH-Z19 Node"
echo "═══════════════════════════════════════════════════════"

# Check ESP-IDF
if [ -z "$IDF_PATH" ]; then
    echo "⚠️  Sourcing ESP-IDF environment..."
    source ~/esp/esp-idf/export.sh
fi

# Build
echo "Building firmware..."
idf.py build

# Flash
echo ""
echo "Flashing to $PORT..."
idf.py -p $PORT flash

echo ""
echo "✓ Flash complete!"
echo ""
echo "To monitor output:"
echo "  idf.py -p $PORT monitor"
echo ""
echo "Or use screen:"
echo "  screen $PORT 115200"
echo ""
