#!/bin/bash
echo "=========================================="
echo "ESP32-CAM Hardware Diagnostics"
echo "=========================================="
echo ""

echo "1. Checking FTDI connection..."
if lsusb | grep -i "FTDI\|Future Technology" > /dev/null; then
    echo "   ✅ FTDI adapter detected"
    lsusb | grep -i "FTDI\|Future Technology"
else
    echo "   ❌ FTDI adapter NOT found"
fi
echo ""

echo "2. Checking serial port..."
if [ -e /dev/ttyUSB1 ]; then
    echo "   ✅ /dev/ttyUSB1 exists"
    ls -l /dev/ttyUSB1
else
    echo "   ❌ /dev/ttyUSB1 not found"
fi
echo ""

echo "3. Testing serial port access..."
if echo "test" > /dev/ttyUSB1 2>/dev/null; then
    echo "   ✅ Can write to serial port"
else
    echo "   ❌ Cannot write to serial port (permission issue?)"
fi
echo ""

echo "4. Checking for ESP32 bootloader messages..."
echo "   Listening for 3 seconds... (press RESET button now if GPIO0 grounded)"
stty -F /dev/ttyUSB1 115200
timeout 3 cat /dev/ttyUSB1 2>/dev/null | strings | head -10 || echo "   ❌ No data received from ESP32-CAM"
echo ""

echo "5. Recent USB events..."
dmesg | grep -i "ttyUSB1\|FTDI" | tail -5
echo ""

echo "=========================================="
echo "RECOMMENDATIONS:"
echo "=========================================="
echo ""
echo "If you see '❌ No data received from ESP32-CAM':"
echo "  1. Check power supply is connected and LED is ON"
echo "  2. Verify TX/RX wiring (should be crossed)"
echo "  3. Try different GPIO0 timing:"
echo "     - Ground GPIO0 FIRST"
echo "     - THEN press and release RESET"
echo "     - Keep GPIO0 grounded"
echo "  4. Measure voltage with multimeter (should be 5V)"
echo ""
echo "If power supply is from Raspberry Pi USB:"
echo "  ⚠️  Use phone charger (2A) instead - Pi USB may be insufficient"
echo ""
