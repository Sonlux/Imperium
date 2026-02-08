#!/bin/bash
# Comprehensive demo menu test

cd /home/imperium/Imperium

echo "=========================================="
echo "Testing Demo Menu - All Options"
echo "=========================================="

# Test 1: Check API Health (option 2)
echo -e "\n[TEST 1] Option 2: Check API Health"
timeout 10 python3 scripts/demo_menu.py <<< $'2\n\nq\n' 2>&1 | grep -A 3 "API Health Check" || echo "✗ Failed"

# Test 2: Submit Example Intent (option 3, example 1)
echo -e "\n[TEST 2] Option 3: Submit Example Intent"
timeout 15 python3 scripts/demo_menu.py <<< $'3\n1\n\nq\n' 2>&1 | grep -E "(prioritize|Intent submitted)" || echo "✗ Failed"

# Test 3: Custom Intent with ESP32 (option 4)
echo -e "\n[TEST 3] Option 4: Custom Intent (ESP32)"
timeout 15 python3 scripts/demo_menu.py <<< $'4\nset sample rate to 48000 hz for esp32-audio-1\n\nq\n' 2>&1 | grep -E "(Intent|ESP32)" || echo "✗ Failed"

# Test 4: Docker Status (option 7)
echo -e "\n[TEST 4] Option 7: Docker Containers"
timeout 10 python3 scripts/demo_menu.py <<< $'7\n\nq\n' 2>&1 | grep -A 3 "Docker" || echo "✗ Failed"

# Test 5: System Overview (option 9)
echo -e "\n[TEST 5] Option 9: System Overview"
timeout 10 python3 scripts/demo_menu.py <<< $'9\n\nq\n' 2>&1 | grep -A 3 "System" || echo "✗ Failed"

# Test 6: IoT Node Menu (option 12)
echo -e "\n[TEST 6] Option 12: IoT Node Menu"
timeout 10 python3 scripts/demo_menu.py <<< $'12\nb\nq\n' 2>&1 | grep "IOT NODE MANAGEMENT" && echo "✓ Passed" || echo "✗ Failed"

# Test 7: List IoT Nodes (option 12->2)
echo -e "\n[TEST 7] Option 12->2: List Running Nodes"
timeout 15 python3 scripts/demo_menu.py <<< $'12\n2\n\nb\nq\n' 2>&1 | grep -E "(Simulated Nodes|Hardware Nodes|esp32-audio-1)" && echo "✓ Passed" || echo "✗ Failed"

# Test 8: ESP32 Menu Access (option 12->e)
echo -e "\n[TEST 8] Option 12->e: ESP32 Menu Access"
timeout 15 python3 scripts/demo_menu.py <<< $'12\ne\nb\nb\nq\n' 2>&1 | grep "ESP32 AUDIO NODE" && echo "✓ Passed" || echo "✗ Failed"

# Test 9: ESP32 Metrics (option 12->e->1)
echo -e "\n[TEST 9] Option 12->e->1: ESP32 View Metrics"
timeout 20 python3 scripts/demo_menu.py <<< $'12\ne\n1\n\nb\nb\nq\n' 2>&1 | grep -E "(Sample Rate|Audio Gain|responding)" && echo "✓ Passed" || echo "✗ Failed"

# Test 10: ESP32 Intent Examples (option 12->e->6)
echo -e "\n[TEST 10] Option 12->e->6: ESP32 Intent Examples"
timeout 20 python3 scripts/demo_menu.py <<< $'12\ne\n6\n\nb\nb\nq\n' 2>&1 | grep -E "(Sample Rate Control|Audio Gain|Publish Interval)" && echo "✓ Passed" || echo "✗ Failed"

echo -e "\n=========================================="
echo "Demo Menu Test Summary"
echo "=========================================="
echo "All basic tests completed."
echo "Check output above for any ✗ Failed tests."
