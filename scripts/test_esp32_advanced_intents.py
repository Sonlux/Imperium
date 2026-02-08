#!/usr/bin/env python3
"""
ESP32 Advanced Intent Integration Test
Tests publish_interval and audio_gain controls
Validates Prometheus metrics changes
"""
import sys
import time
import requests
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from intent_manager.parser import IntentParser
from policy_engine.engine import PolicyEngine
from enforcement.device import DeviceEnforcer

ESP32_IP = "10.218.189.218"
ESP32_METRICS_URL = f"http://{ESP32_IP}:8080/metrics"
DEVICE_ID = "esp32-audio-1"

def check_esp32_online():
    """Verify ESP32 is reachable"""
    try:
        resp = requests.get(ESP32_METRICS_URL, timeout=2)
        return resp.status_code == 200
    except:
        return False

def get_metric_value(metric_name):
    """Extract metric value from Prometheus endpoint"""
    try:
        resp = requests.get(ESP32_METRICS_URL, timeout=2)
        for line in resp.text.split('\n'):
            if line.startswith(metric_name):
                # Parse: metric_name{device="esp32-audio-1"} value
                value = line.split('}')[1].strip()
                return float(value)
        return None
    except Exception as e:
        print(f"  ⚠️  Error getting {metric_name}: {e}")
        return None

def test_intent(intent_text, metric_name, expected_value, wait_time=10, tolerance=0.1, enforcer=None):
    """Test a single intent and validate metric change"""
    print(f"\n{'='*60}")
    print(f"TEST: {intent_text}")
    print(f"{'='*60}")
    print(f"Intent: \"{intent_text}\"")
    
    # Parse intent
    parser = IntentParser()
    parsed = parser.parse(intent_text)
    print(f"  Parsed Type: {parsed.get('type')}")
    print(f"  Parameters: {parsed.get('parameters')}")
    
    # Generate policy
    engine = PolicyEngine()
    policies = engine.generate_policies(parsed)
    print(f"Generated {len(policies)} policy(ies):")
    
    if len(policies) == 0:
        print(f"  ❌ FAIL - No policies generated!")
        return False
    
    for p in policies:
        print(f"  - Type: {p.policy_type.value}, Target: {p.target}")
        print(f"    Params: {p.parameters}")
    
    # Apply policy
    if enforcer is None:
        enforcer = DeviceEnforcer()
        enforcer.connect()
        time.sleep(2)  # Wait for connection
    
    print(f"\nApplying policy: {policies[0].policy_id}")
    result = enforcer.apply_policy(policies[0].to_dict())
    print(f"  Apply result: {'✅ Success' if result else '❌ Failed'}")
    
    # Wait for enforcement
    print(f"\n⏳ Waiting {wait_time} seconds for policy enforcement...")
    time.sleep(wait_time)
    
    # Verify metric
    print(f"\n📊 Verification:")
    actual_value = get_metric_value(metric_name)
    
    if actual_value is None:
        print(f"  ❌ FAIL - Could not read {metric_name}")
        return False
    
    print(f"  Expected: {metric_name} = {expected_value}")
    print(f"  Actual: {metric_name} = {actual_value}")
    
    # Check if within tolerance
    if isinstance(expected_value, (int, float)):
        if abs(actual_value - expected_value) <= tolerance:
            print(f"  ✅ PASS - Value matches!")
            return True
        else:
            print(f"  ❌ FAIL - Value differs by {abs(actual_value - expected_value)}")
            return False
    
    return False

def main():
    print("="*60)
    print("🧪 IMPERIUM ESP32 ADVANCED INTENT TEST")
    print("="*60)
    print()
    
    # Check connectivity
    print("📡 Checking ESP32 connectivity...")
    if not check_esp32_online():
        print("❌ ESP32 is offline! Cannot run tests.")
        return 1
    
    print("✅ ESP32 is online and responding\n")
    
    # Get initial state
    print("📊 Initial State:")
    publish_interval = get_metric_value("telemetry_publish_interval_ms")
    audio_gain = get_metric_value("audio_gain_multiplier")
    print(f"  Publish Interval: {publish_interval} ms")
    print(f"  Audio Gain: {audio_gain}x")
    
    # Create single enforcer instance
    print("\n🔌 Connecting to MQTT broker...")
    enforcer = DeviceEnforcer()
    enforcer.connect()
    time.sleep(2)
    print("✅ Connected to MQTT broker\n")
    
    results = []
    
    # Test 1: Change publish interval to 5 seconds
    results.append(test_intent(
        "Set telemetry rate to 5 seconds for esp32-audio-1",
        "telemetry_publish_interval_ms",
        5000.0,
        wait_time=8,
        enforcer=enforcer
    ))
    
    # Test 2: Set audio gain to 2x amplification
    results.append(test_intent(
        "Set audio gain to 2.0 for esp32-audio-1",
        "audio_gain_multiplier",
        2.0,
        wait_time=8,
        enforcer=enforcer
    ))
    
    # Test 3: Very frequent telemetry (1 second)
    results.append(test_intent(
        "Report telemetry every 1 second for esp32-audio-1",
        "telemetry_publish_interval_ms",
        1000.0,
        wait_time=8,
        enforcer=enforcer
    ))
    
    # Test 4: Reduce gain to 0.5x (quieter)
    results.append(test_intent(
        "Reduce audio volume to 0.5 for esp32-audio-1",
        "audio_gain_multiplier",
        0.5,
        wait_time=8,
        enforcer=enforcer
    ))
    
    # Test 5: Slow telemetry (30 seconds)
    results.append(test_intent(
        "Set publish interval to 30000 ms for esp32-audio-1",
        "telemetry_publish_interval_ms",
        30000.0,
        wait_time=8,
        enforcer=enforcer
    ))
    
    # Test 6: Boost audio significantly (5x)
    results.append(test_intent(
        "Amplify audio by 5x for esp32-audio-1",
        "audio_gain_multiplier",
        5.0,
        wait_time=8,
        enforcer=enforcer
    ))
    
    # Test 7: Reset to defaults (10 seconds, 1.0x gain)
    results.append(test_intent(
        "Reset device esp32-audio-1",
        "telemetry_publish_interval_ms",
        10000.0,
        wait_time=10,
        enforcer=enforcer
    ))
    
    # Verify gain also reset
    time.sleep(2)
    gain_after_reset = get_metric_value("audio_gain_multiplier")
    gain_reset_ok = abs(gain_after_reset - 1.0) < 0.1
    results.append(gain_reset_ok)
    print(f"\n  Audio gain after reset: {gain_after_reset}x {'✅' if gain_reset_ok else '❌'}")
    
    # Cleanup
    enforcer.disconnect()
    
    # Summary
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
