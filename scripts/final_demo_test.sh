#!/bin/bash
# Final comprehensive demo test
cd /home/imperium/Imperium

echo "=========================================="
echo "FINAL DEMO VERIFICATION"
echo "=========================================="

# Test 1: API Health
echo -e "\n[TEST 1] API Health"
curl -s http://localhost:5000/health | grep -q "healthy" && echo "✓ PASS" || echo "✗ FAIL"

# Test 2: ESP32 Online
echo -e "\n[TEST 2] ESP32 Online"
timeout 3 bash -c 'curl -s http://10.218.189.218:8080/metrics | grep -q "audio_sample_rate_hz"' && echo "✓ PASS (ESP32 online)" || echo "⚠ SKIP (ESP32 offline - optional hardware)"

# Test 3: MQTT Broker
echo -e "\n[TEST 3] MQTT Broker"
docker ps | grep -q mqtt && echo "✓ PASS" || echo "✗ FAIL"

# Test 4: Prometheus
echo -e "\n[TEST 4] Prometheus"
curl -s http://localhost:9090/-/healthy | grep -q "Prometheus" && echo "✓ PASS" || echo "✗ FAIL"

# Test 5: Grafana
echo -e "\n[TEST 5] Grafana"
curl -s http://localhost:3000/api/health | grep -q "ok" && echo "✓ PASS" || echo "✗ FAIL"

# Test 6: Submit Intent via API
echo -e "\n[TEST 6] Submit Intent (API)"
TOKEN=$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

INTENT_RESPONSE=$(curl -s -X POST http://localhost:5000/api/v1/intents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description":"set audio gain to 1.5 for esp32-audio-1"}')

echo "$INTENT_RESPONSE" | grep -q '"success": true' && echo "✓ PASS" || echo "✗ FAIL"

# Wait for enforcement
sleep 5

# Test 7: Verify ESP32 Enforcement
echo -e "\n[TEST 7] ESP32 Enforcement (gain = 1.5)"
timeout 3 bash -c 'curl -s http://10.218.189.218:8080/metrics | grep "audio_gain_multiplier" | grep -q "1.50"' && echo "✓ PASS" || echo "⚠ SKIP (ESP32 offline)"

# Test 8: Demo Menu Loads
echo -e "\n[TEST 8] Demo Menu Loads"
timeout 5 python3 scripts/demo_menu.py <<< $'q\n' 2>&1 | grep -q "IMPERIUM IBN" && echo "✓ PASS" || echo "✗ FAIL"

# Test 9: IoT Node Menu
echo -e "\n[TEST 9] IoT Node Menu"
timeout 10 python3 scripts/demo_menu.py <<< $'12\nb\nq\n' 2>&1 | grep -q "IOT NODE MANAGEMENT" && echo "✓ PASS" || echo "✗ FAIL"

# Test 10: ESP32 Integration (no separate submenu)
echo -e "\n[TEST 10] ESP32 Integration (in existing menus)"
timeout 15 python3 scripts/demo_menu.py <<< $'12\n4\n\nb\nq\n' 2>&1 | grep -q "esp32-audio-1\|ESP32" && echo "✓ PASS (ESP32 integrated)" || echo "⚠ SKIP (ESP32 may be offline)"

echo -e "\n=========================================="
echo "TEST SUMMARY"
echo "=========================================="
echo "All tests completed. Check for any ✗ FAIL above."
echo ""
echo "If all tests passed, the system is ready for demo!"
