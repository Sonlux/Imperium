#!/bin/bash
echo "=== Manual Flash - Uncompressed (Lowest Power Consumption) ==="
echo "Make sure GPIO0 is connected to GND and press RESET button now!"
read -p "Press Enter when ready..." 

echo "Step 1/3: Flashing bootloader (no compression)..."
python3 -m esptool --chip esp32 --port /dev/ttyUSB1 --baud 115200 \
  --before no_reset --after no_reset \
  write_flash --flash_mode dio --flash_freq 40m --flash_size 4MB \
  0x1000 build/bootloader/bootloader.bin || exit 1

echo "Step 2/3: Flashing partition table..."
python3 -m esptool --chip esp32 --port /dev/ttyUSB1 --baud 115200 \
  --before no_reset --after no_reset \
  write_flash 0x8000 build/partition_table/partition-table.bin || exit 1

echo "Step 3/3: Flashing main firmware (THIS WILL TAKE ~15 MINUTES)..."
python3 -m esptool --chip esp32 --port /dev/ttyUSB1 --baud 115200 \
  --before no_reset --after hard_reset \
  write_flash 0x10000 build/esp32-cam-node.bin

echo "=== Flash Complete! Remove GPIO0 jumper and press RESET ==="
