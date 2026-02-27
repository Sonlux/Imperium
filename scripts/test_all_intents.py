#!/usr/bin/env python3
"""
Comprehensive intent testing for ALL Imperium intent types against ALL node types.
Tests: simulated nodes → CO2/audio → ESP32-CAM
"""
import requests
import json
import time
import sys
import subprocess
import threading
import paho.mqtt.client as mqtt

API = "http://localhost:5000"
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# ── Colours ──────────────────────────────────────────────
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Collect MQTT messages for verification
mqtt_messages = []
mqtt_lock = threading.Lock()

# Topics to SKIP (binary data, noisy telemetry)
SKIP_TOPICS = ("/images", "/data", "/telemetry")

def mqtt_on_message(client, userdata, msg):
    # Skip binary/noisy topics
    if any(s in msg.topic for s in SKIP_TOPICS):
        return
    try:
        payload = msg.payload.decode("utf-8")
    except UnicodeDecodeError:
        return  # skip binary payloads
    with mqtt_lock:
        mqtt_messages.append({
            "topic": msg.topic,
            "payload": payload,
            "ts": time.time()
        })

def start_mqtt_monitor():
    c = mqtt.Client(client_id="test-monitor")
    c.on_message = mqtt_on_message
    c.connect(MQTT_BROKER, MQTT_PORT, 60)
    # Subscribe only to control/status topics — avoid binary image floods
    c.subscribe([
        ("iot/+/control", 0),
        ("iot/+/status", 0),
        ("imperium/devices/+/control", 0),
        ("imperium/policy/#", 0),
    ])
    c.loop_start()
    return c

def get_recent_mqtt(topic_contains=None, since=None, payload_contains=None):
    """Get MQTT messages matching criteria."""
    with mqtt_lock:
        msgs = list(mqtt_messages)
    results = []
    for m in msgs:
        if since and m["ts"] < since:
            continue
        if topic_contains and topic_contains not in m["topic"]:
            continue
        if payload_contains and payload_contains not in m["payload"]:
            continue
        results.append(m)
    return results


def get_token():
    r = requests.post(f"{API}/api/v1/auth/login",
                      json={"username": "admin", "password": "admin"}, timeout=5)
    return r.json()["token"]


def submit_intent(token, description):
    """Submit an intent and return the parsed result."""
    r = requests.post(
        f"{API}/api/v1/intents",
        json={"description": description},
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=10,
    )
    return r.json()


def check_tc_class(classid):
    """Check if a tc class exists."""
    out = subprocess.run(["sudo", "tc", "class", "show", "dev", "wlan0"],
                         capture_output=True, text=True)
    return f"1:{classid} " in out.stdout


def check_tc_netem(classid):
    """Check if netem qdisc exists under a class."""
    out = subprocess.run(["sudo", "tc", "qdisc", "show", "dev", "wlan0"],
                         capture_output=True, text=True)
    return f"parent 1:{classid}" in out.stdout and "netem" in out.stdout


def clear_tc():
    subprocess.run(["sudo", "tc", "qdisc", "del", "dev", "wlan0", "root"],
                   capture_output=True)


# ── Test runner ──────────────────────────────────────────
results = {"pass": 0, "fail": 0, "warn": 0}


def test(name, intent_text, checks, token):
    """Run a single intent test with verification checks."""
    ts_before = time.time()
    print(f"\n  {CYAN}▶ {name}{RESET}")
    print(f"    Intent: \"{intent_text}\"")

    resp = submit_intent(token, intent_text)
    time.sleep(1.5)  # Wait for enforcement

    if not resp.get("success"):
        print(f"    {RED}✗ API returned error: {resp.get('error', resp)}{RESET}")
        results["fail"] += 1
        return resp

    intent = resp.get("intent", {})
    parsed_type = intent.get("parsed", {}).get("type", "?")
    n_policies = len(intent.get("policies", []))
    policy_types = [p.get("policy_type", "?") for p in intent.get("policies", [])]

    print(f"    Parsed type: {parsed_type} | Policies: {n_policies} → {policy_types}")

    all_ok = True
    for desc, check_fn in checks:
        try:
            ok = check_fn(resp, ts_before)
        except Exception as e:
            ok = False
            print(f"    {RED}✗ {desc}: exception {e}{RESET}")
        if ok:
            print(f"    {GREEN}✓ {desc}{RESET}")
        else:
            print(f"    {RED}✗ {desc}{RESET}")
            all_ok = False

    if all_ok:
        results["pass"] += 1
    else:
        results["fail"] += 1

    return resp


# ── Check helpers ────────────────────────────────────────
def has_policies(n):
    def _check(resp, ts):
        return len(resp.get("intent", {}).get("policies", [])) >= n
    return _check

def has_type(expected):
    def _check(resp, ts):
        return resp.get("intent", {}).get("parsed", {}).get("type") == expected
    return _check

def policy_type_present(ptype):
    def _check(resp, ts):
        return any(p.get("policy_type") == ptype for p in resp.get("intent", {}).get("policies", []))
    return _check

def mqtt_sent_to(topic_part, payload_part=None):
    def _check(resp, ts):
        time.sleep(0.5)
        msgs = get_recent_mqtt(topic_contains=topic_part, since=ts, payload_contains=payload_part)
        if msgs:
            print(f"      → MQTT: {msgs[0]['topic']} | {msgs[0]['payload'][:120]}")
        return len(msgs) > 0
    return _check

def tc_class_exists(cid):
    def _check(resp, ts):
        return check_tc_class(cid)
    return _check

def tc_netem_exists(cid):
    def _check(resp, ts):
        return check_tc_netem(cid)
    return _check


# ══════════════════════════════════════════════════════════
#                    MAIN TEST SEQUENCE
# ══════════════════════════════════════════════════════════
def main():
    print(f"\n{BOLD}{'='*60}")
    print(" Imperium — Comprehensive Intent Test Suite")
    print(f"{'='*60}{RESET}\n")

    # Setup
    mqtt_client = start_mqtt_monitor()
    time.sleep(1)
    token = get_token()
    print(f"  Auth token acquired ✓")

    # ────────────────────────────────────────────────────
    # PHASE 1: SIMULATED NODES (node-1 to node-10)
    # ────────────────────────────────────────────────────
    print(f"\n{BOLD}{YELLOW}━━━ PHASE 1: SIMULATED IoT NODES ━━━{RESET}")
    print(f"  Nodes: node-1 through node-10 (Docker)")
    print(f"  MQTT topic: iot/node-X/control")
    print(f"  Capabilities: qos, sampling_rate, priority, enabled, latency\n")

    # 1.1 QoS control
    test("QoS level 2 for node-1", "set qos level 2 for node-1", [
        ("Parsed as qos", has_type("qos")),
        ("Policy generated", has_policies(1)),
        ("MQTT sent to iot/node-1", mqtt_sent_to("iot/node-1/control", "qos")),
    ], token)

    # 1.2 QoS with reliable delivery
    test("Reliable delivery for node-3", "reliable delivery for node-3", [
        ("Parsed as qos", has_type("qos")),
        ("MQTT sent to node-3", mqtt_sent_to("iot/node-3/control")),
    ], token)

    # 1.3 Device control - enable
    test("Enable node-5", "enable device node-5", [
        ("Parsed as device_control", has_type("device_control")),
        ("Policy generated", has_policies(1)),
        ("Policy type is device_control", policy_type_present("device_control")),
        ("MQTT sent to node-5", mqtt_sent_to("iot/node-5/control", "ENABLE")),
    ], token)

    # 1.4 Device control - disable
    test("Disable node-2", "disable node-2", [
        ("Parsed as device_control", has_type("device_control")),
        ("MQTT sent to node-2", mqtt_sent_to("iot/node-2/control", "DISABLE")),
    ], token)

    # 1.5 Device control - reset
    test("Reset node-7", "reset device node-7", [
        ("Parsed as device_control", has_type("device_control")),
        ("MQTT sent to node-7", mqtt_sent_to("iot/node-7/control", "RESET")),
    ], token)

    # 1.6 Priority (network — expect policy but no TC since no registry)
    test("Prioritize node-1 (network)", "prioritize node-1", [
        ("Parsed as priority", has_type("priority")),
        ("Policies generated", has_policies(1)),
    ], token)

    # ────────────────────────────────────────────────────
    # PHASE 2: ESP32-MHZ19 CO2 NODE
    # ────────────────────────────────────────────────────
    print(f"\n{BOLD}{YELLOW}━━━ PHASE 2: ESP32 CO₂ SENSOR (esp32-mhz19-1) ━━━{RESET}")
    print(f"  IP: 10.218.189.218 | TC classid: 20")
    print(f"  MQTT: imperium/devices/esp32-mhz19-1/control")
    print(f"  Capabilities: sampling_interval, qos, bandwidth, latency, priority\n")

    # 2.1 Sampling interval
    test("CO2 sampling every 30s", "set sampling interval for esp32-mhz19-1 to 30 seconds", [
        ("Parsed as sampling_interval", has_type("sampling_interval")),
        ("Policy generated", has_policies(1)),
        ("MQTT to imperium/devices/esp32-mhz19-1", mqtt_sent_to("imperium/devices/esp32-mhz19-1/control", "SET_PUBLISH_INTERVAL")),
    ], token)

    # 2.2 CO2 every N seconds (alternative phrasing)
    test("Read CO2 every 10 seconds", "read co2 every 10 seconds for esp32-mhz19-1", [
        ("Parsed as sampling_interval", has_type("sampling_interval")),
        ("MQTT sent", mqtt_sent_to("imperium/devices/esp32-mhz19-1/control", "SET_PUBLISH_INTERVAL")),
    ], token)

    # 2.3 QoS for CO2
    test("QoS 2 for esp32-mhz19-1", "set qos level 2 for esp32-mhz19-1", [
        ("Parsed as qos", has_type("qos")),
        ("MQTT sent to mhz19", mqtt_sent_to("imperium/devices/esp32-mhz19-1/control", "SET_QOS")),
    ], token)

    # 2.4 Bandwidth limit (network)
    clear_tc()
    test("Limit CO2 bandwidth to 1mbit", "limit bandwidth to 1mbit for esp32-mhz19-1", [
        ("Parsed as bandwidth", has_type("bandwidth")),
        ("Policy generated", has_policies(1)),
        ("TC class 1:20 created", tc_class_exists(20)),
    ], token)

    # 2.5 Latency injection (network)
    test("Add 50ms latency to CO2", "add latency of 50ms for esp32-mhz19-1", [
        ("Parsed as latency", has_type("latency")),
        ("Netem on class 20", tc_netem_exists(20)),
    ], token)

    # 2.6 Priority (network)
    test("High priority for CO2", "set high priority for esp32-mhz19-1", [
        ("Parsed as priority", has_type("priority")),
        ("TC class 1:20 exists", tc_class_exists(20)),
    ], token)

    # 2.7 Device control - reset
    test("Reset CO2 sensor", "reset esp32-mhz19-1", [
        ("Parsed as device_control", has_type("device_control")),
        ("MQTT sent", mqtt_sent_to("imperium/devices/esp32-mhz19-1/control", "RESET")),
    ], token)

    # ────────────────────────────────────────────────────
    # PHASE 3: ESP32-AUDIO NODE
    # ────────────────────────────────────────────────────
    print(f"\n{BOLD}{YELLOW}━━━ PHASE 3: ESP32 AUDIO NODE (esp32-audio-1) ━━━{RESET}")
    print(f"  IP: 10.218.189.218 (shared w/ CO2) | TC classid: 20")
    print(f"  MQTT: iot/esp32-audio-1/control")
    print(f"  Capabilities: sample_rate, audio_gain, publish_interval, qos, device_control\n")

    # 3.1 Sample rate
    test("Audio sample rate 48kHz", "set sample rate to 48000 hz for esp32-audio-1", [
        ("Parsed as sample_rate", has_type("sample_rate")),
        ("Policy generated", has_policies(1)),
        ("MQTT sent to iot/esp32-audio-1", mqtt_sent_to("iot/esp32-audio-1/control", "SET_SAMPLE_RATE")),
    ], token)

    # 3.2 Sample rate (kHz shorthand)
    test("Audio 16kHz sampling", "16 khz sampling for esp32-audio-1", [
        ("Parsed as sample_rate", has_type("sample_rate")),
        ("MQTT sent", mqtt_sent_to("iot/esp32-audio-1/control", "SET_SAMPLE_RATE")),
    ], token)

    # 3.3 Audio gain
    test("Audio gain 3.5x", "set audio gain to 3.5 for esp32-audio-1", [
        ("Parsed as audio_gain", has_type("audio_gain")),
        ("Policy generated", has_policies(1)),
        ("MQTT sent to audio node", mqtt_sent_to("iot/esp32-audio-1/control", "SET_AUDIO_GAIN")),
    ], token)

    # 3.4 Boost audio
    test("Boost audio 2x", "amplify audio by 2x for esp32-audio-1", [
        ("Parsed as audio_gain", has_type("audio_gain")),
        ("MQTT sent", mqtt_sent_to("iot/esp32-audio-1/control", "SET_AUDIO_GAIN")),
    ], token)

    # 3.5 Publish interval
    test("Publish every 5 seconds", "send data every 5 seconds for esp32-audio-1", [
        ("Parsed as publish_interval", has_type("publish_interval")),
        ("MQTT sent to audio", mqtt_sent_to("iot/esp32-audio-1/control", "SET_PUBLISH_INTERVAL")),
    ], token)

    # 3.6 QoS for audio
    test("QoS 1 for audio", "qos level 1 for esp32-audio-1", [
        ("Parsed as qos", has_type("qos")),
        ("MQTT sent to iot/esp32-audio-1", mqtt_sent_to("iot/esp32-audio-1/control")),
    ], token)

    # 3.7 Enable/disable audio
    test("Disable audio node", "disable esp32-audio-1", [
        ("Parsed as device_control", has_type("device_control")),
        ("MQTT sent w/ DISABLE", mqtt_sent_to("iot/esp32-audio-1/control", "DISABLE")),
    ], token)

    test("Enable audio node", "enable esp32-audio-1", [
        ("Parsed as device_control", has_type("device_control")),
        ("MQTT sent w/ ENABLE", mqtt_sent_to("iot/esp32-audio-1/control", "ENABLE")),
    ], token)

    # 3.8 Bandwidth for audio (network — shares classid 20 with CO2)
    clear_tc()
    test("Limit audio bandwidth 500kbit", "limit bandwidth to 500kbit for esp32-audio-1", [
        ("Parsed as bandwidth", has_type("bandwidth")),
        ("TC class 1:20 created", tc_class_exists(20)),
    ], token)

    # ────────────────────────────────────────────────────
    # PHASE 4: ESP32-CAM NODE
    # ────────────────────────────────────────────────────
    print(f"\n{BOLD}{YELLOW}━━━ PHASE 4: ESP32-CAM (esp32-cam-1) ━━━{RESET}")
    print(f"  IP: 10.218.189.80 | TC classid: 10")
    print(f"  MQTT: iot/esp32-cam-1/control")
    print(f"  Capabilities: resolution, quality, brightness, framerate, camera_control,")
    print(f"                qos, bandwidth, latency, priority\n")

    # 4.1 Camera resolution
    test("Camera VGA resolution", "set resolution to VGA for esp32-cam-1", [
        ("Parsed as camera_resolution", has_type("camera_resolution")),
        ("Policy generated", has_policies(1)),
        ("MQTT sent to cam", mqtt_sent_to("iot/esp32-cam-1/control", "resolution")),
    ], token)

    # 4.2 Camera HD
    test("Camera HD resolution", "change to HD resolution for esp32-cam-1", [
        ("Parsed as camera_resolution", has_type("camera_resolution")),
        ("MQTT sent", mqtt_sent_to("iot/esp32-cam-1/control", "HD")),
    ], token)

    # 4.3 Camera UXGA
    test("Camera UXGA (full HD)", "set resolution to UXGA for esp32-cam-1", [
        ("Parsed as camera_resolution", has_type("camera_resolution")),
        ("MQTT sent", mqtt_sent_to("iot/esp32-cam-1/control", "UXGA")),
    ], token)

    # 4.4 Camera quality numeric
    test("Camera quality 10", "set camera quality to 10 for esp32-cam-1", [
        ("Parsed as camera_quality", has_type("camera_quality")),
        ("MQTT sent", mqtt_sent_to("iot/esp32-cam-1/control", "quality")),
    ], token)

    # 4.5 Camera quality preset
    test("Camera quality 5 (high)", "set camera quality to 5 for esp32-cam-1", [
        ("Parsed as camera_quality", has_type("camera_quality")),
        ("MQTT sent", mqtt_sent_to("iot/esp32-cam-1/control", "quality")),
    ], token)

    # 4.6 Camera brightness
    test("Camera brightness +1", "set camera brightness to 1 for esp32-cam-1", [
        ("Parsed as camera_brightness", has_type("camera_brightness")),
        ("MQTT sent", mqtt_sent_to("iot/esp32-cam-1/control", "brightness")),
    ], token)

    # 4.7 Camera framerate
    test("Camera 5 FPS", "set camera fps to 5 for esp32-cam-1", [
        ("Parsed as camera_framerate", has_type("camera_framerate")),
        ("MQTT sent", mqtt_sent_to("iot/esp32-cam-1/control", "capture_interval")),
    ], token)

    # 4.8 Capture interval
    test("Capture every 3 seconds", "capture every 3 seconds for esp32-cam-1", [
        ("Parsed as camera_framerate", has_type("camera_framerate")),
        ("MQTT sent", mqtt_sent_to("iot/esp32-cam-1/control", "capture_interval")),
    ], token)

    # 4.9 Camera disable/enable
    test("Disable camera", "disable camera for esp32-cam-1", [
        ("Parsed as camera_control", has_type("camera_control")),
        ("MQTT sent", mqtt_sent_to("iot/esp32-cam-1/control", "enabled")),
    ], token)

    test("Enable camera", "enable camera for esp32-cam-1", [
        ("Parsed as camera_control", has_type("camera_control")),
        ("MQTT sent", mqtt_sent_to("iot/esp32-cam-1/control", "enabled")),
    ], token)

    # 4.10 Bandwidth (network)
    clear_tc()
    test("Limit cam bandwidth 2mbit", "limit bandwidth to 2mbit for esp32-cam-1", [
        ("Parsed as bandwidth", has_type("bandwidth")),
        ("TC class 1:10 created", tc_class_exists(10)),
    ], token)

    # 4.11 Latency injection (network)
    test("Add 100ms latency to cam", "add latency of 100ms for esp32-cam-1", [
        ("Parsed as latency", has_type("latency")),
        ("Netem on class 10", tc_netem_exists(10)),
    ], token)

    # 4.12 High priority (network)
    test("High priority for cam", "set high priority for esp32-cam-1", [
        ("Parsed as priority", has_type("priority")),
        ("TC class 1:10 exists", tc_class_exists(10)),
    ], token)

    # 4.13 Low latency (network — different path: traffic_shaping)
    clear_tc()
    test("Minimize latency for cam", "minimize latency for esp32-cam-1", [
        ("Parsed as latency", has_type("latency")),
        ("Policy generated", has_policies(1)),
        ("TC class 1:10 created", tc_class_exists(10)),
    ], token)

    # 4.14 Camera QoS
    test("Camera QoS 2", "set qos level 2 for esp32-cam-1", [
        ("Parsed as qos", has_type("qos")),
        ("MQTT sent to cam", mqtt_sent_to("iot/esp32-cam-1/control")),
    ], token)

    # Clean up
    clear_tc()

    # ────────────────────────────────────────────────────
    # SUMMARY
    # ────────────────────────────────────────────────────
    total = results["pass"] + results["fail"]
    print(f"\n{BOLD}{'='*60}")
    print(f" TEST RESULTS: {results['pass']}/{total} passed")
    print(f"{'='*60}{RESET}")
    print(f"  {GREEN}✓ Passed: {results['pass']}{RESET}")
    print(f"  {RED}✗ Failed: {results['fail']}{RESET}")

    mqtt_client.loop_stop()
    mqtt_client.disconnect()

    return 0 if results["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
