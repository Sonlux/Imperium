# ESP32-CAM Flash Troubleshooting Guide

## Current Issue: "Failed to connect to ESP32: No serial data received"

### Hardware Checklist:

1. **Power Supply** (CRITICAL):
   - [ ] ESP32-CAM connected to external 5V supply (2A minimum)
   - [ ] GND from power supply connected to ESP32-CAM GND
   - [ ] Power LED on ESP32-CAM is ON (red LED near camera)
   - [ ] NO power from FTDI adapter (only data signals)

2. **FTDI Wiring**:
   ```
   FTDI TX  → ESP32-CAM U0R (RX)
   FTDI RX  → ESP32-CAM U0T (TX)
   FTDI GND → ESP32-CAM GND (common ground with power supply)
   ```
   - [ ] TX and RX are CROSSED (not straight through)
   - [ ] GND connected to both power supply and FTDI

3. **Bootloader Mode**:
   - [ ] GPIO0 pin connected to GND with jumper wire
   - [ ] Press RESET button while GPIO0 grounded
   - [ ] White flash LED should blink briefly
   - [ ] Keep GPIO0 grounded during entire flash process

### Alternative Flash Method (If Above Fails):

**Try using Arduino IDE instead:**

1. Install Arduino IDE: `sudo apt install arduino`
2. Add ESP32 board support:
   - File → Preferences → Additional Boards Manager URLs
   - Add: `https://dl.espressif.com/dl/package_esp32_index.json`
3. Tools → Board → ESP32 Arduino → AI Thinker ESP32-CAM
4. Tools → Port → /dev/ttyUSB1
5. Upload speed → 115200
6. Upload a simple sketch first (File → Examples → Basic → Blink)

### Power Supply Test:

```bash
# Check if voltage is stable during flash
# You need a multimeter to measure voltage at ESP32-CAM 5V and GND pins
# Should stay at 4.8-5.2V even during flash operations
```

### Last Resort - Hardware Issues:

1. **Bad FTDI adapter**: Try different USB port or different FTDI adapter
2. **Damaged ESP32-CAM**: Previous overheating may have damaged board
3. **Bad USB cable**: Try different cable
4. **Insufficient power**: Use phone charger (2A rated) instead of PC USB

### What We Know Works:
- ✅ ESP32-CAM powered on (got hot, so it's alive)
- ✅ FTDI adapter detected by Linux
- ✅ Previously achieved 70% flash (bootloader complete)
- ❌ Now can't enter bootloader mode at all

### Most Likely Issues:
1. **Power supply degraded** or voltage dropping under load
2. **GPIO0 connection loose** - not making proper contact
3. **RESET button not working** properly
