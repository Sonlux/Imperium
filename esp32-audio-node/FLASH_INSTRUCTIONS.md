# Flash ESP32 from Windows PC

## Method 1: Using ESP-IDF on Windows

If you have ESP-IDF installed on Windows:

```powershell
# Copy the binary from Raspberry Pi
scp imperium@raspberrypi.local:~/Imperium/esp32-audio-node/build/esp32-audio-node.bin .
scp imperium@raspberrypi.local:~/Imperium/esp32-audio-node/build/bootloader/bootloader.bin .
scp imperium@raspberrypi.local:~/Imperium/esp32-audio-node/build/partition_table/partition-table.bin .

# Flash using esptool (adjust COM port)
esptool.py --chip esp32 --port COM3 --baud 460800 write_flash -z 0x1000 bootloader.bin 0x8000 partition-table.bin 0x10000 esp32-audio-node.bin
```

## Method 2: Use esptool directly (simpler)

Install esptool: `pip install esptool`

```powershell
# Navigate to where you copied the files
esptool.py -p COM3 -b 460800 --before default_reset --after hard_reset --chip esp32 write_flash --flash_mode dio --flash_size 2MB --flash_freq 40m 0x1000 bootloader.bin 0x8000 partition-table.bin 0x10000 esp32-audio-node.bin
```

## Method 3: Connect ESP32 to Raspberry Pi

Simply connect the ESP32 USB cable to the Raspberry Pi and run:

```bash
cd ~/Imperium/esp32-audio-node
source ~/esp/esp-idf/export.sh
idf.py -p /dev/ttyUSB0 flash monitor
```

## After Flashing

The ESP32 will:
1. Boot up (takes ~5-10 seconds)
2. Connect to WiFi "Galaxy A56 5G A76A"
3. Start publishing to MQTT broker at 10.218.189.192
4. Be accessible at http://10.218.189.218:8080/metrics

Then you can test the sample rate intent!
