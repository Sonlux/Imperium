#!/usr/bin/env python3
"""
ESP32 Audio Node - Intent-Based Networking Demo
Tests the full IBN cycle: Intent → Policy → Enforcement → Feedback
"""

import requests
import json
import time
import paho.mqtt.client as mqtt
from datetime import datetime

IMPERIUM_API = "http://localhost:5000"
MQTT_BROKER = "localhost"
ESP32_DEVICE = "esp32-audio-1"
ESP32_IP = "10.218.189.218"

# Track telemetry
telemetry_data = []

def on_message(client, userdata, msg):
    """Capture telemetry messages"""
    try:
        data = json.loads(msg.payload.decode())
        telemetry_data.append(data)
    except:
        pass

def get_esp32_metrics():
    """Fetch current ESP32 metrics"""
    try:
        response = requests.get(f"http://{ESP32_IP}:8080/metrics", timeout=3)
        metrics = {}
        for line in response.text.split('\n'):
            if 'audio_sample_rate_hz' in line and not line.startswith('#'):
                metrics['sample_rate'] = int(line.split()[-1])
            elif 'mqtt_qos_level' in line and not line.startswith('#'):
                metrics['qos'] = int(line.split()[-1])
            elif 'audio_frames_captured_total' in line and not line.startswith('#'):
                metrics['frames'] = int(line.split()[-1])
        return metrics
    except Exception as e:
        return {"error": str(e)}

def submit_intent(intent_text):
    """Submit intent to Imperium API"""
    print(f"\n📝 Submitting Intent: '{intent_text}'")
    
    try:
        response = requests.post(
            f"{IMPERIUM_API}/api/intent",
            json={"intent": intent_text},
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Intent accepted: {result.get('intent_id', 'N/A')}")
            return result
        else:
            print(f"❌ Intent failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ API Error: {e}")
        return None

def send_mqtt_command(command, **params):
    """Send direct MQTT command to ESP32"""
    print(f"\n📤 Sending MQTT Command: {command}")
    
    client = mqtt.Client()
    client.connect(MQTT_BROKER, 1883, 60)
    
    payload = {"command": command, **params}
    topic = f"iot/{ESP32_DEVICE}/control"
    
    client.publish(topic, json.dumps(payload), qos=1)
    print(f"   → {payload}")
    
    client.disconnect()
    time.sleep(2)

def verify_policy_enforcement(expected_rate=None, expected_qos=None):
    """Verify policy was applied by checking metrics"""
    print(f"\n🔍 Verifying Policy Enforcement...")
    time.sleep(3)
    
    metrics = get_esp32_metrics()
    
    if "error" in metrics:
        print(f"   ⚠️  Could not fetch metrics: {metrics['error']}")
        return False
    
    success = True
    
    if expected_rate:
        actual_rate = metrics.get('sample_rate', 0)
        if actual_rate == expected_rate:
            print(f"   ✅ Sample Rate: {actual_rate} Hz (expected {expected_rate})")
        else:
            print(f"   ❌ Sample Rate: {actual_rate} Hz (expected {expected_rate})")
            success = False
    
    if expected_qos:
        actual_qos = metrics.get('qos', 0)
        if actual_qos == expected_qos:
            print(f"   ✅ QoS Level: {actual_qos} (expected {expected_qos})")
        else:
            print(f"   ❌ QoS Level: {actual_qos} (expected {expected_qos})")
            success = False
    
    print(f"   📊 Total Frames: {metrics.get('frames', 'N/A')}")
    
    return success

def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  ESP32 Intent-Based Networking Demo                    ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"\n⏰ Started at {datetime.now().strftime('%H:%M:%S')}")
    
    # Setup MQTT subscriber
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(MQTT_BROKER, 1883, 60)
    client.subscribe(f"iot/{ESP32_DEVICE}/telemetry")
    client.loop_start()
    
    # Get baseline metrics
    print("\n📊 Baseline Metrics:")
    baseline = get_esp32_metrics()
    print(f"   Sample Rate: {baseline.get('sample_rate', 'N/A')} Hz")
    print(f"   QoS Level: {baseline.get('qos', 'N/A')}")
    print(f"   Frames Captured: {baseline.get('frames', 'N/A')}")
    
    # Test 1: Reduce audio quality (lower sample rate)
    print("\n" + "="*60)
    print("TEST 1: Intent to reduce bandwidth usage")
    print("="*60)
    
    send_mqtt_command("SET_SAMPLE_RATE", sample_rate=8000)
    verify_policy_enforcement(expected_rate=8000)
    
    time.sleep(5)
    
    # Test 2: Prioritize audio (increase QoS)
    print("\n" + "="*60)
    print("TEST 2: Intent to prioritize audio reliability")
    print("="*60)
    
    send_mqtt_command("SET_QOS", qos=2)
    verify_policy_enforcement(expected_qos=2)
    
    time.sleep(5)
    
    # Test 3: High quality audio
    print("\n" + "="*60)
    print("TEST 3: Intent for high quality audio capture")
    print("="*60)
    
    send_mqtt_command("SET_SAMPLE_RATE", sample_rate=16000)
    send_mqtt_command("SET_QOS", qos=1)
    verify_policy_enforcement(expected_rate=16000, expected_qos=1)
    
    # Show telemetry summary
    print("\n📈 Telemetry Summary:")
    print(f"   Received {len(telemetry_data)} telemetry messages")
    if telemetry_data:
        latest = telemetry_data[-1]
        print(f"   Latest RMS: {latest.get('rms_db', 'N/A')} dB")
        print(f"   Buffer Overruns: {latest.get('buffer_overruns', 'N/A')}")
        print(f"   Uptime: {latest.get('uptime_ms', 0)/1000:.1f}s")
    
    client.loop_stop()
    
    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║  ✅ Intent-Based Networking Demo Complete               ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    print("\n💡 Next Steps:")
    print("   • Create Grafana dashboard for ESP32 metrics")
    print("   • Add ESP32 to intent parser grammar")
    print("   • Implement feedback loop for auto-adjustment")
    print("   • Test multi-device policy orchestration")

if __name__ == "__main__":
    main()
