# Imperium: Cognitive Edge-Orchestrated IBN Framework

## Project Overview

This is an **Intent-Based Networking (IBN) framework** for edge/IoT environments running on Raspberry Pi. It translates high-level user intents (e.g., "prioritize sensor-A" or "reduce latency for device-X") into real-time network policies using Linux traffic control, MQTT device commands, and closed-loop feedback.

**Key Technologies:** Python, MQTT (Mosquitto), Prometheus, Grafana, Docker, Linux `tc`/`netem`/`iptables`, ESP32 nodes (physical/simulated).

## Project Status

⚠️ **Implementation Phase:** Only README and task list exist. All code modules are pending implementation per [task.md](../docs/development/task.md).

## Architecture Components

### 1. Intent Layer

- **Intent Acquisition API** (FastAPI REST endpoints) - receives high-level user goals
- **Intent Parser** - NLTK-based NLP + rule extraction to convert natural language to structured parameters (priority, latency targets, bandwidth limits, device IDs)

### 2. Policy Engine

- Transforms parsed intents into actionable network policies
- Generates: traffic shaping rules (`tc htb`, `netem`), MQTT QoS levels, routing priorities, sampling rate adjustments
- Policy representation format: TBD (JSON/YAML config structure)

### 3. Enforcement Layer

- **Network Enforcement** - applies `tc` commands for bandwidth/latency control on Raspberry Pi interfaces
- **Device Enforcement** - publishes MQTT commands to IoT nodes (ESP32/Docker simulators)
- Target enforcement latency: 200-500ms

### 4. Feedback Loop

- **Monitoring** - Prometheus scrapes metrics (latency, throughput, packet delivery) from exporters
- **Feedback Engine** - compares live metrics vs. intent goals, triggers policy adjustments if deviation detected
- **Grafana Dashboards** - real-time visualization of network state changes

### 5. IoT Nodes

- **ESP32 devices** (physical hardware) + **Docker simulators** (for testing)
- Subscribe to MQTT topics for policy updates (QoS changes, sampling frequency, bandwidth limits)
- Publish telemetry data

## Development Guidelines

### Module Structure (Proposed)

```
src/
├── intent/           # Intent acquisition & parsing
├── policy/           # Policy generation & representation
├── enforcement/      # Network (tc) & device (MQTT) enforcement
├── feedback/         # Metric collection & self-correction logic
├── nodes/            # IoT node simulators (Dockerized)
└── api/              # REST API for intent submission
```

### Key Dependencies

- **Python 3.9+** - primary language for control plane
- **FastAPI** - REST API framework for intent submission endpoint
- **NLTK** - natural language processing for intent parser
- **Mosquitto** - MQTT broker for device messaging
- **Prometheus + Grafana** - monitoring stack
- **Docker** - for IoT node simulation and service orchestration
- **Linux tools** - `tc`, `iproute2`, `iptables` (pre-installed on Raspberry Pi OS)

### Critical Implementation Patterns

#### Intent Parsing Example

Intent: `"Prioritize temperature sensors and limit bandwidth to 100KB/s for cameras"`
→ Parsed to: `{priority: ["temp-*"], bandwidth: {"camera-*": "100KB/s"}}`
→ Policy: `tc qdisc add htb ...` + MQTT publish to camera nodes

#### Policy Enforcement Workflow

1. Policy Engine generates config: `{"device": "temp-01", "qos": 2, "sampling_hz": 10}`
2. Enforcement Module executes:
   - Network: `tc filter add ... flowid 1:10` (high priority queue)
   - Device: MQTT publish to `devices/temp-01/config`

#### Feedback Loop Cycle

1. Prometheus scrapes `/metrics` endpoint every 5s
2. Feedback Engine queries Prometheus: `rate(latency[30s]) > intent_target`
3. If violated → adjust policy → re-enforce → verify convergence

### Resource Constraints

- **Target Platform:** Raspberry Pi 4 (4-8GB RAM)
- **CPU Budget:** Keep <60% sustained (policy generation/enforcement should be O(n) in device count)
- **Memory:** Limit Python processes to <500MB each
- **Network:** Optimize for edge bandwidth (avoid verbose logging over network)

### Testing Strategy

1. **Unit Tests** - parser logic, policy generation rules
2. **Integration Tests** - MQTT round-trip, `tc` command application, Prometheus queries
3. **System Tests** - end-to-end intent → policy → enforcement → metrics → feedback
4. **Load Tests** - validate with 50+ simulated IoT nodes

### MQTT Topic Structure

**Device Control Topics:**

- `imperium/devices/{device_id}/config` - policy updates (QoS, bandwidth, sampling rate)
- `imperium/devices/{device_id}/telemetry` - device metrics (publish)
- `imperium/devices/{device_id}/status` - online/offline heartbeat

**System Topics:**

- `imperium/intent/new` - intent submission (alternative to REST API)
- `imperium/policy/applied` - enforcement notifications
- `imperium/feedback/alert` - metric violations

### Configuration Management

- Use YAML for policy templates, device registry, intent grammar rules
- Environment variables for service endpoints (MQTT broker URL, Prometheus API, Grafana)
- Example: `config/devices.yaml` with node IDs, capabilities, QoS profiles

### Monitoring & Observability

- **Grafana Dashboards** should show:
  - Per-device latency/throughput (time-series)
  - Policy enforcement timeline (events overlay)
  - Intent satisfaction score (computed metric)
  - System resource usage (Raspberry Pi CPU/memory)
- Export custom Prometheus metrics: `ibs_intent_satisfaction_ratio`, `ibs_policy_enforcement_latency_seconds`

## Common Workflows

### Adding a New Intent Type

1. Update parser grammar in `src/intent/parser.py` (e.g., add "reduce jitter" intent)
2. Extend policy generator with corresponding rule (use `tc netem delay` with variance)
3. Add metrics exporter for jitter measurement
4. Update Grafana dashboard with jitter panel

### Docker Compose Structure

**Primary Services** (`docker-compose.yml`):

- `mosquitto` - MQTT broker (port 1883, optional TLS 8883)
- `prometheus` - metrics storage (port 9090, scrape interval 5s)
- `grafana` - visualization (port 3000, pre-configured dashboards)
- `ibs-controller` - main Python app (FastAPI on port 8000)

**Node Simulators** (`docker-compose.nodes.yml`):

- `iot-node` - scaled service (subscribes to `imperium/devices/+/config`)

### Deploying to Raspberry Pi

```bash
# SSH into Pi, clone repo, install deps
sudo apt-get install -y python3-venv
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
docker compose up -d  # Start MQTT/Prometheus/Grafana
uvicorn src.main:app --host 0.0.0.0 --port 8000  # Launch IBN controller
```

### Simulating IoT Nodes

```bash
docker compose -f docker-compose.nodes.yml up --scale iot-node=10
# Each node subscribes to MQTT, generates traffic, responds to policy commands
```

## Critical Implementation Gaps (Check task.md)

- [ ] NLTK training data for intent classification (need corpus of sample intents)
- [ ] FastAPI authentication middleware (JWT tokens or API keys)
- [ ] Policy conflict resolution (e.g., two intents affect same device)
- [ ] Security: MQTT TLS certificates, secure WebSocket for Grafana
- [ ] Persistence: SQLite/PostgreSQL for intent history and policy state

## Resources

- **Linux Traffic Control:** [man tc](https://man7.org/linux/man-pages/man8/tc.8.html), [tc-htb](https://man7.org/linux/man-pages/man8/tc-htb.8.html)
- **MQTT Paho Python:** [eclipse.org/paho](https://www.eclipse.org/paho/clients/python/)
- **Prometheus Python Client:** [github.com/prometheus/client_python](https://github.com/prometheus/client_python)
