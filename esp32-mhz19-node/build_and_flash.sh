#!/bin/bash
# Complete Build and Flash Process for ESP32 MH-Z19 Node

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  ESP32 MH-Z19 CO2 Sensor - Complete Build Process${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if running from correct directory
if [ ! -f "main/main.c" ]; then
    print_error "Please run this script from esp32-mhz19-node directory"
    exit 1
fi

print_status "In correct directory"

# Step 1: Check ESP-IDF
echo ""
echo "Step 1: Checking ESP-IDF installation..."
if [ -z "$IDF_PATH" ]; then
    print_warning "ESP-IDF environment not set"
    
    # Try to source it
    if [ -f "$HOME/esp/esp-idf/export.sh" ]; then
        print_info "Found ESP-IDF, sourcing environment..."
        source "$HOME/esp/esp-idf/export.sh"
        print_status "ESP-IDF environment loaded"
    else
        print_error "ESP-IDF not found. Please install it first:"
        echo ""
        echo "  mkdir -p ~/esp"
        echo "  cd ~/esp"
        echo "  git clone --recursive https://github.com/espressif/esp-idf.git"
        echo "  cd esp-idf"
        echo "  ./install.sh esp32"
        echo "  source export.sh"
        exit 1
    fi
else
    print_status "ESP-IDF found: $IDF_PATH"
fi

# Step 2: Hardware check
echo ""
echo "Step 2: Hardware Connection Check"
echo "═══════════════════════════════════"
echo ""
echo "Please verify your wiring:"
echo "  MH-Z19 VCC → ESP32 5V (VIN)"
echo "  MH-Z19 GND → ESP32 GND"
echo "  MH-Z19 TX  → ESP32 GPIO16 (RX2)"
echo "  MH-Z19 RX  → ESP32 GPIO17 (TX2)"
echo ""
read -p "Is the hardware connected correctly? (y/n): " hardware_ok
if [ "$hardware_ok" != "y" ]; then
    print_warning "Please connect hardware first, then run this script again"
    exit 0
fi
print_status "Hardware verified"

# Step 3: Detect serial port
echo ""
echo "Step 3: Detecting ESP32 serial port..."
if [ -e /dev/ttyUSB0 ]; then
    PORT="/dev/ttyUSB0"
    print_status "Found ESP32 at $PORT"
elif [ -e /dev/ttyUSB1 ]; then
    PORT="/dev/ttyUSB1"
    print_status "Found ESP32 at $PORT"
elif [ -e /dev/ttyACM0 ]; then
    PORT="/dev/ttyACM0"
    print_status "Found ESP32 at $PORT"
else
    print_warning "No serial device found"
    read -p "Enter serial port manually (e.g., /dev/ttyUSB0): " PORT
fi

# Check port permissions
if [ ! -w "$PORT" ]; then
    print_warning "No write permission for $PORT"
    print_info "Adding user to dialout group..."
    sudo usermod -a -G dialout $USER
    print_warning "Please logout and login again, then re-run this script"
    exit 0
fi

# Step 4: Configuration
echo ""
echo "Step 4: Configuration"
echo "═══════════════════════════════════"
read -p "Configure WiFi and MQTT now? (y/n): " config_now
if [ "$config_now" = "y" ]; then
    ./setup_esp.sh
    print_status "Configuration updated"
else
    print_warning "Using existing configuration from main/config.h"
fi

# Step 5: Clean previous build
echo ""
echo "Step 5: Cleaning previous build..."
if [ -d "build" ]; then
    print_info "Removing old build directory..."
    rm -rf build
fi
print_status "Clean complete"

# Step 6: Build firmware
echo ""
echo "Step 6: Building firmware..."
echo "This may take 3-5 minutes on first build..."
echo ""

if idf.py build; then
    print_status "Build successful!"
else
    print_error "Build failed. Check errors above."
    exit 1
fi

# Check firmware size
FIRMWARE_SIZE=$(ls -lh build/*.bin | head -1 | awk '{print $5}')
print_info "Firmware size: $FIRMWARE_SIZE"

# Step 7: Flash firmware
echo ""
echo "Step 7: Flashing firmware to ESP32..."
echo "═══════════════════════════════════"
print_warning "Press and hold BOOT button on ESP32 if flash fails"
echo ""

if idf.py -p $PORT flash; then
    print_status "Flash successful!"
else
    print_error "Flash failed. Try these solutions:"
    echo "  1. Press and hold BOOT button while connecting"
    echo "  2. Try: esptool.py --port $PORT erase_flash"
    echo "  3. Check USB cable (must support data transfer)"
    exit 1
fi

# Step 8: Optional monitoring
echo ""
echo "Step 8: Monitor output (optional)"
echo "═══════════════════════════════════"
read -p "Start serial monitor now? (y/n): " monitor_now

if [ "$monitor_now" = "y" ]; then
    echo ""
    print_info "Starting monitor (Ctrl+] to exit)..."
    echo ""
    sleep 2
    idf.py -p $PORT monitor
else
    echo ""
    print_info "To monitor later, run:"
    echo "  idf.py -p $PORT monitor"
fi

# Summary
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Build and Flash Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo "Next steps:"
echo "  1. Monitor: idf.py -p $PORT monitor"
echo "  2. Watch for sensor warm-up (3 minutes)"
echo "  3. Test MQTT: mosquitto_sub -t 'imperium/devices/+/telemetry'"
echo "  4. Submit intent via Imperium API"
echo ""
print_info "See INTEGRATION.md for Imperium integration guide"
print_info "See TROUBLESHOOTING.md if you encounter issues"
echo ""
