#!/bin/bash
# ESP32 Audio Node - Quick Demo Script

echo "═══════════════════════════════════════════════════════"
echo "  ESP32 Audio Node - Imperium Integration Demo"
echo "═══════════════════════════════════════════════════════"
echo ""

# Check ESP32 connectivity
echo "1️⃣  Checking ESP32 connectivity..."
if ping -c 1 -W 2 10.218.189.218 &>/dev/null; then
    echo "   ✅ ESP32 online at 10.218.189.218"
else
    echo "   ❌ ESP32 offline - check WiFi connection"
    exit 1
fi
echo ""

# Check metrics endpoint
echo "2️⃣  Fetching ESP32 metrics..."
if curl -s --max-time 3 http://10.218.189.218:8080/metrics &>/dev/null; then
    FRAMES=$(curl -s http://10.218.189.218:8080/metrics | grep "audio_frames_captured_total" | awk '{print $2}')
    RMS=$(curl -s http://10.218.189.218:8080/metrics | grep "audio_rms_level_db" | awk '{print $2}')
    QOS=$(curl -s http://10.218.189.218:8080/metrics | grep "mqtt_qos_level" | awk '{print $2}')
    RATE=$(curl -s http://10.218.189.218:8080/metrics | grep "audio_sample_rate_hz" | awk '{print $2}')
    
    echo "   📊 Frames Captured: $FRAMES"
    echo "   🎤 RMS Level: ${RMS} dB"
    echo "   📡 MQTT QoS: $QOS"
    echo "   🎵 Sample Rate: ${RATE} Hz"
else
    echo "   ❌ Metrics endpoint not responding"
    exit 1
fi
echo ""

# Check MQTT messages
echo "3️⃣  Monitoring MQTT telemetry (5 seconds)..."
timeout 5 mosquitto_sub -h localhost -t "iot/esp32-audio-1/telemetry" -C 1 2>/dev/null | \
    python3 -c "import sys, json; d=json.loads(sys.stdin.read()); print(f\"   ✅ Device: {d['device_id']}\"); print(f\"   📈 Uptime: {d['uptime_ms']/1000:.1f}s\"); print(f\"   🎯 Buffer Overruns: {d['buffer_overruns']}\")" 2>/dev/null || echo "   ⚠️  No telemetry received"
echo ""

# Check Prometheus scraping
echo "4️⃣  Verifying Prometheus integration..."
PROM_DATA=$(curl -s 'http://localhost:9090/api/v1/query?query=audio_frames_captured_total' 2>/dev/null)
if echo "$PROM_DATA" | grep -q "audio_frames_captured_total"; then
    PROM_FRAMES=$(echo "$PROM_DATA" | python3 -c "import sys, json; r=json.load(sys.stdin)['data']['result']; print(r[0]['value'][1] if r else '0')" 2>/dev/null)
    echo "   ✅ Prometheus collecting ESP32 metrics"
    echo "   📊 Frames in Prometheus: $PROM_FRAMES"
else
    echo "   ⚠️  Prometheus not scraping ESP32 yet"
fi
echo ""

# Policy control test
echo "5️⃣  Testing policy control..."
read -p "   Test changing sample rate to 8000Hz? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "   📤 Sending SET_SAMPLE_RATE command..."
    mosquitto_pub -h localhost -t "iot/esp32-audio-1/control" \
        -m '{"command":"SET_SAMPLE_RATE","sample_rate":8000}'
    
    echo "   ⏳ Waiting 10 seconds for policy to apply..."
    sleep 10
    
    NEW_RATE=$(curl -s http://10.218.189.218:8080/metrics | grep "audio_sample_rate_hz" | awk '{print $2}')
    echo "   📊 New sample rate: ${NEW_RATE} Hz"
    
    # Restore to 16000
    echo "   🔄 Restoring to 16000 Hz..."
    mosquitto_pub -h localhost -t "iot/esp32-audio-1/control" \
        -m '{"command":"SET_SAMPLE_RATE","sample_rate":16000}'
    sleep 2
    echo "   ✅ Restored to default"
else
    echo "   ⏭️  Skipping policy test"
fi
echo ""

echo "═══════════════════════════════════════════════════════"
echo "  Demo Complete!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "📖 More info: cat /home/imperium/Imperium/esp32-audio-node/INTEGRATION_COMPLETE.md"
echo "📊 Grafana: http://localhost:3000"
echo "📈 Prometheus: http://localhost:9090"
echo "🎤 Metrics: http://10.218.189.218:8080/metrics"
echo ""
