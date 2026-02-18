#!/bin/bash
echo "=== ESP32-CAM Power Cycle Flash Procedure ==="
echo ""
echo "The board may be stuck from incomplete flash. Let's recover it."
echo ""
echo "STEP 1: Full power cycle"
echo "  1. DISCONNECT 5V power from ESP32-CAM"
echo "  2. Wait 5 seconds"
echo "  3. RECONNECT 5V power"
echo "  4. Red LED should turn on"
echo ""
read -p "Press Enter when power is RECONNECTED and red LED is ON..."
echo ""
echo "STEP 2: Enter bootloader mode"
echo "  1. Connect GPIO0 to GND with jumper wire"
echo "  2. Press and HOLD RESET button for 2 seconds"
echo "  3. Release RESET (keep GPIO0 grounded)"
echo ""
read -p "Press Enter IMMEDIATELY after releasing RESET button..."
echo ""
echo "STEP 3: Attempting flash with multiple retries..."
for i in {1..5}; do
    echo "Attempt $i/5..."
    python3 -m esptool --chip esp32 --port /dev/ttyUSB1 --baud 115200 \
        --before no_reset --after no_reset \
        write_flash --flash_mode dio --flash_freq 40m --flash_size 4MB \
        0x1000 build/bootloader/bootloader.bin \
        0x8000 build/partition_table/partition-table.bin \
        0x10000 build/esp32-cam-node.bin && break
    echo "Failed, retrying in 2 seconds..."
    sleep 2
done
echo ""
echo "If all attempts failed, try power cycle again or check GPIO0 connection quality"
