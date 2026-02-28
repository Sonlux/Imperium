# MH-Z19 Troubleshooting Guide

## Hardware Issues

### Sensor Not Detected

**Symptoms:**
- No UART communication
- Timeout errors in logs
- No response from sensor

**Solutions:**
1. **Check Wiring:**
   ```
   MH-Z19 TX → ESP32 GPIO16 (RX2)
   MH-Z19 RX → ESP32 GPIO17 (TX2)
   ```
   TX goes to RX, RX goes to TX!

2. **Verify Power:**
   - MH-Z19 requires 5V (VIN pin)
   - Check voltage with multimeter: 4.5V-5.5V
   - Ensure adequate current supply (>20mA)

3. **Test UART:**
   ```bash
   # In ESP32 terminal
   uart_read_bytes() should return data
   ```

### Inaccurate Readings

**Problem: CO2 readings are way off (e.g., 10000+ ppm in normal room)**

**Solutions:**
1. **Warm-up Period:**
   - Wait 3 minutes minimum
   - Best accuracy after 24 hours continuous operation

2. **Calibrate Zero Point:**
   - Place sensor in fresh outdoor air (400 ppm)
   - Wait 20 minutes
   - Send calibration command:
   ```bash
   mosquitto_pub -t "imperium/devices/esp32-mhz19-1/control" \
       -m '{"command":"CALIBRATE_ZERO"}'
   ```

3. **Check ABC Mode:**
   - Should be enabled for indoor use
   - Assumes sensor sees 400 ppm daily

4. **Sensor Aging:**
   - MH-Z19 lifespan: 3-5 years
   - Gradual drift is normal
   - Replace if readings unreliable after calibration

### Sensor Freezes

**Symptoms:**
- Same reading repeatedly
- No response to commands

**Solutions:**
1. **Power Cycle:**
   ```bash
   # Disconnect 5V for 10 seconds
   # Reconnect and wait 3 minutes
   ```

2. **Check for Interference:**
   - Keep away from strong magnets
   - Avoid direct sunlight on sensor
   - Ensure proper ventilation

## Software Issues

### Build Errors

**Error: `IDF_PATH` not set**
```bash
# Solution:
source ~/esp/esp-idf/export.sh
# Or add to ~/.bashrc:
alias get_idf='. $HOME/esp/esp-idf/export.sh'
```

**Error: Component not found**
```bash
# Solution:
idf.py reconfigure
idf.py clean
idf.py build
```

**Error: UART driver install failed**
- Check if GPIO pins are already in use
- Verify `sdkconfig` has UART enabled
- Try different GPIO pins in config.h

### Flash Errors

**Error: Failed to connect to ESP32**
```bash
# Solutions:
1. Press and hold BOOT button while connecting
2. Check USB cable (must support data transfer)
3. Verify port: ls /dev/ttyUSB*
4. Add user to dialout group:
   sudo usermod -a -G dialout $USER
   # Logout and login again
```

**Error: Chip not found**
```bash
# Try erasing flash first:
esptool.py --port /dev/ttyUSB0 erase_flash
idf.py -p /dev/ttyUSB0 flash
```

### WiFi Connection Issues

**WiFi not connecting:**
1. **Verify Credentials:**
   - Check SSID/password in `main/config.h`
   - Ensure no special characters causing issues
   - Rebuild after changing config

2. **Check Network:**
   - ESP32 only supports 2.4GHz WiFi
   - Verify router is broadcasting 2.4GHz
   - Check signal strength (move closer)

3. **Check Logs:**
   ```bash
   idf.py monitor | grep WIFI
   ```

**Frequent Disconnections:**
- Weak signal (RSSI < -80 dBm)
- Router issue (try different channel)
- Power supply instability

### MQTT Connection Issues

**MQTT not connecting:**
1. **Verify Broker:**
   ```bash
   # Test broker from PC:
   mosquitto_pub -h 192.168.1.100 -t test -m "hello"
   ```

2. **Check Firewall:**
   ```bash
   # On broker machine:
   sudo ufw allow 1883
   ```

3. **Verify IP Address:**
   - Check broker IP hasn't changed
   - Update `main/config.h` if needed

**Messages not received:**
- Check topic subscription
- Verify QoS level
- Check MQTT logs on broker

## Performance Issues

### High Power Consumption

**Normal:**
- First 3 minutes: High (warm-up)
- After warm-up: ~18mA average

**If excessive:**
1. Reduce publish frequency
2. Check for WiFi reconnection loops
3. Implement sleep mode (requires code modification)

### Slow Response

**Sensor reads slowly:**
- Minimum 2 seconds between reads (MH-Z19 spec)
- Don't query faster than this
- Use async pattern if needed

**MQTT lag:**
- Check network latency
- Verify broker not overloaded
- Use QoS 0 for telemetry if needed

## Data Quality Issues

### Noisy Readings

**CO2 fluctuates wildly:**
1. **Normal Variation:**
   - ±50 ppm is normal
   - Breathing nearby causes spikes
   - Air movement affects readings

2. **Electrical Noise:**
   - Add 100nF capacitor near sensor VCC/GND
   - Use shielded wires for long runs
   - Keep away from motors/relays

### Readings Stuck at Minimum/Maximum

**Always 400 ppm or 5000 ppm:**
- Sensor in error state
- Power cycle required
- May need recalibration
- Check detection range setting

## Debug Commands

### Enable Verbose Logging
Edit `main/config.h`:
```c
#define CONFIG_LOG_DEFAULT_LEVEL_DEBUG
```

### Monitor UART Traffic
```bash
# Raw UART monitoring (PC to MH-Z19):
screen /dev/ttyUSB0 9600

# ESP32 monitor with colors:
idf.py monitor --print-filter="*:V"
```

### Test Sensor Manually
```c
// In main.c, add test function:
void test_sensor() {
    mhz19_data_t data;
    ESP_ERROR_CHECK(mhz19_read_data(&data));
    ESP_LOGI(TAG, "CO2: %u ppm", data.co2_ppm);
}
```

### Check MQTT Messages
```bash
# Subscribe to all topics:
mosquitto_sub -h 192.168.1.100 -v -t "imperium/devices/esp32-mhz19-1/#"

# Monitor with timestamps:
mosquitto_sub -h 192.168.1.100 -v -t "imperium/devices/+/telemetry" | while read line; do echo "[$(date +%T)] $line"; done
```

## Advanced Diagnostics

### Checksum Errors
```
I (xxx) MHZ19: Checksum verification failed
```
**Causes:**
- Electrical noise
- Baud rate mismatch
- Loose connections
- Damaged sensor

**Solutions:**
- Check wiring integrity
- Add 100nF capacitor
- Replace sensor if persistent

### Memory Issues
```
E (xxx) MAIN: Failed to allocate memory
```
**Solutions:**
- Increase task stack size in config.h
- Reduce JSON buffer size
- Check for memory leaks

### Watchdog Timeout
```
E (xxx) task_wdt: Task watchdog got triggered
```
**Solutions:**
- Increase `CONFIG_ESP_TASK_WDT_TIMEOUT_S`
- Check for blocking operations
- Add `vTaskDelay()` in long loops

## Getting Help

### Collect Debug Information
```bash
# Save full log:
idf.py monitor > debug.log 2>&1

# Get system info:
idf.py monitor
# Type: Ctrl+T, then 'i'

# Check memory:
# Type: Ctrl+T, then 'm'
```

### Useful Logs to Share
1. Full boot sequence
2. WiFi connection logs
3. MQTT connection logs
4. Sensor read attempts
5. Error messages with timestamps

### Contact Support
Include:
- Hardware: ESP32 model, MH-Z19 version
- Software: ESP-IDF version, firmware version
- Logs: Boot sequence, error messages
- Environment: WiFi strength, MQTT broker details
