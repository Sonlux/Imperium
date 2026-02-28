#!/bin/bash
# ESP32 Sample Rate Dynamic Intent Test - COMPLETE

echo "🧪 ESP32 Sample Rate Intent Test"
echo "================================="
echo ""

# Function to get current sample rate
get_sample_rate() {
    curl -s --max-time 3 http://10.218.189.218:8080/metrics | grep "audio_sample_rate_hz{" | awk -F' ' '{print $2}'
}

# Test 1: Change to 8kHz
echo "Test 1: Changing sample rate to 8kHz..."
mosquitto_pub -h localhost -t "iot/esp32-audio-1/control" -m '{"command":"SET_SAMPLE_RATE","sample_rate":8000}' -q 1
echo "⏳ Waiting 12 seconds for I2S driver reconfiguration..."
sleep 12

SR=$(get_sample_rate)
if [ "$SR" = "8000" ]; then
    echo "✅ SUCCESS: Sample rate changed to 8kHz"
else
    echo "❌ FAILED: Sample rate is $SR Hz (expected 8000)"
fi

echo ""
sleep 2

# Test 2: Change to 16kHz
echo "Test 2: Changing sample rate to 16kHz..."
mosquitto_pub -h localhost -t "iot/esp32-audio-1/control" -m '{"command":"SET_SAMPLE_RATE","sample_rate":16000}' -q 1
echo "⏳ Waiting 12 seconds for I2S driver reconfiguration..."
sleep 12

SR=$(get_sample_rate)
if [ "$SR" = "16000" ]; then
    echo "✅ SUCCESS: Sample rate changed to 16kHz"
else
    echo "❌ FAILED: Sample rate is $SR Hz (expected 16000)"
fi

echo ""
sleep 2

# Test 3: Change to 44.1kHz
echo "Test 3: Changing sample rate to 44.1kHz..."
mosquitto_pub -h localhost -t "iot/esp32-audio-1/control" -m '{"command":"SET_SAMPLE_RATE","sample_rate":44100}' -q 1
echo "⏳ Waiting 12 seconds for I2S driver reconfiguration..."
sleep 12

SR=$(get_sample_rate)
if [ "$SR" = "44100" ]; then
    echo "✅ SUCCESS: Sample rate changed to 44.1kHz"
else
    echo "❌ FAILED: Sample rate is $SR Hz (expected 44100)"
fi

echo ""
sleep 2

# Test 4: Change to 48kHz
echo "Test 4: Changing sample rate to 48kHz..."
mosquitto_pub -h localhost -t "iot/esp32-audio-1/control" -m '{"command":"SET_SAMPLE_RATE","sample_rate":48000}' -q 1
echo "⏳ Waiting 12 seconds for I2S driver reconfiguration..."
sleep 12

SR=$(get_sample_rate)
if [ "$SR" = "48000" ]; then
    echo "✅ SUCCESS: Sample rate changed to 48kHz"
else
    echo "❌ FAILED: Sample rate is $SR Hz (expected 48000)"
fi

echo ""
echo "🎯 Test Complete - ESP32 stability check..."
ping -c 3 -W 1 10.218.189.218 > /dev/null && echo "✅ ESP32 online and stable" || echo "❌ ESP32 offline"
echo ""
echo "Final sample rate: $(get_sample_rate) Hz"
