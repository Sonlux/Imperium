#!/usr/bin/env python3
"""
ESP32 Intent Integration Test
Tests all Imperium intents on the ESP32 audio node
"""
import sys
import os
import time
import json
import requests

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from intent_manager.parser import IntentParser
from policy_engine.engine import PolicyEngine
from enforcement.device import DeviceEnforcer

ESP32_IP = "10.218.189.218"
ESP32_METRICS_URL = f"http://{ESP32_IP}:8080/metrics"
ESP32_DEVICE_ID = "esp32-audio-1"

def get_esp32_metric(metric_name):
    """Get a specific metric from ESP32"""
    try:
        response = requests.get(ESP32_METRICS_URL, timeout=3)
        for line in response.text.split('\n'):
            if metric_name in line and not line.startswith('#'):
                return line.split()[-1]
    except Exception as e:
        print(f"  ❌ Error getting metrics: {e}")
    return None

def check_esp32_online():
    """Check if ESP32 is online"""
    try:
        response = requests.get(ESP32_METRICS_URL, timeout=3)
        return response.status_code == 200
    except:
        return False

def run_test(test_name, intent_text, expected_metric=None, expected_value=None, wait_time=12):
    """Run a single intent test"""
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"{'='*60}")
    print(f"Intent: \"{intent_text}\"")
    
    # Parse intent
    parser = IntentParser()
    parsed = parser.parse(intent_text)
    print(f"Parsed Type: {parsed['type']}")
    print(f"Parameters: {parsed['parameters']}")
    
    # Generate policy
    engine = PolicyEngine()
    policies = engine.generate_policies(parsed)
    
    if not policies:
        print("  ❌ No policies generated")
        return False
    
    print(f"Generated {len(policies)} policy(ies):")
    for p in policies:
        print(f"  - Type: {p.policy_type.value}, Target: {p.target}")
        print(f"    Params: {p.parameters}")
    
    # Apply policy
    enforcer = DeviceEnforcer('localhost', 1883)
    try:
        enforcer.connect()
        
        for policy in policies:
            policy_dict = policy.to_dict()
            print(f"\nApplying policy: {policy_dict['policy_id']}")
            result = enforcer.apply_policy(policy_dict)
            print(f"  Apply result: {'✅ Success' if result else '❌ Failed'}")
        
        # Wait for policy to take effect
        print(f"\n⏳ Waiting {wait_time} seconds for policy enforcement...")
        time.sleep(wait_time)
        
        # Verify result if expected metric provided
        if expected_metric and expected_value:
            actual = get_esp32_metric(expected_metric)
            print(f"\n📊 Verification:")
            print(f"  Expected: {expected_metric} = {expected_value}")
            print(f"  Actual: {expected_metric} = {actual}")
            
            if str(actual) == str(expected_value):
                print("  ✅ PASS - Value matches!")
                return True
            else:
                print("  ❌ FAIL - Value mismatch!")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    finally:
        enforcer.disconnect()

def main():
    print("=" * 60)
    print("🧪 IMPERIUM ESP32 INTENT INTEGRATION TEST")
    print("=" * 60)
    
    # Check ESP32 is online
    print("\n📡 Checking ESP32 connectivity...")
    if not check_esp32_online():
        print("❌ ESP32 is offline! Cannot run tests.")
        return 1
    print("✅ ESP32 is online and responding")
    
    # Get initial state
    initial_sample_rate = get_esp32_metric("audio_sample_rate_hz")
    initial_qos = get_esp32_metric("mqtt_qos_level")
    print(f"\n📊 Initial State:")
    print(f"  Sample Rate: {initial_sample_rate} Hz")
    print(f"  QoS Level: {initial_qos}")
    
    results = []
    
    # Test 1: Sample Rate Intent
    results.append(run_test(
        "Sample Rate Change (Natural Language)",
        "Set sample rate to 8000 hz for esp32-audio-1",
        "audio_sample_rate_hz",
        "8000"
    ))
    
    # Test 2: QoS Intent
    results.append(run_test(
        "QoS Level Change",
        "Set QoS level 2 for esp32-audio-1",
        "mqtt_qos_level",
        "2",
        wait_time=5
    ))
    
    # Test 3: Another Sample Rate (different phrasing)
    results.append(run_test(
        "Sample Rate (Alternative Phrasing)",
        "Change sampling rate to 48khz for esp32-audio-1",
        "audio_sample_rate_hz",
        "48000"
    ))
    
    # Test 4: QoS back to 1
    results.append(run_test(
        "QoS Reset",
        "Set QoS 1 for esp32-audio-1",
        "mqtt_qos_level",
        "1",
        wait_time=5
    ))
    
    # Test 5: High Sample Rate
    results.append(run_test(
        "High Quality Audio (44.1kHz)",
        "Audio rate 48000 for esp32-audio-1",
        "audio_sample_rate_hz",
        "44100"
    ))
    
    # Test 6: Device Control (Reset to defaults)
    results.append(run_test(
        "Device Reset",
        "Reset device esp32-audio-1",
        None,
        None,
        wait_time=8
    ))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r)
    total = len(results)
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
