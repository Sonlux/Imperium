# Imperium Codebase Index

**Generated:** 2025-01-01  
**Status:** 95% Implementation Complete  
**Platform:** Windows (Development) → Raspberry Pi (Production)

## Repository Structure

```
Imperium/
├── .github/
│   └── copilot-instructions.md      # GitHub Copilot guidance
├── config/
│   ├── devices.yaml                 # Device registry (6 devices, QoS profiles)
│   ├── intent_grammar.yaml          # NLP patterns (7 intent types, 30+ patterns)
│   └── policy_templates.yaml        # tc/netem templates (20+ commands)
├── monitoring/
│   └── grafana/
│       └── provisioning/
│           └── dashboards/
│               ├── dashboard.yml
│               ├── imperium-dev-dashboard.json     # 17 panels
│               └── imperium-overview.json          # System overview
├── scripts/
│   └── test_api.py                  # API testing utility
├── src/
│   ├── enforcement/
│   │   ├── device.py                # MQTT device controller (188 lines)
│   │   └── network.py               # tc/iptables wrapper (211 lines, Linux-only)
│   ├── feedback/
│   │   └── monitor.py               # Prometheus integration (280 lines)
│   ├── intent_manager/
│   │   ├── api.py                   # Flask REST API (165 lines, 5 endpoints)
│   │   └── parser.py                # Regex intent parser (129 lines)
│   ├── iot_simulator/
│   │   └── node.py                  # Dockerized simulator (184 lines)
│   ├── policy_engine/
│   │   └── engine.py                # Policy generator (214 lines)
│   └── main.py                      # Main orchestrator (313 lines)
├── tests/
│   ├── test_core.py                 # Unit tests (112 lines)
│   └── test_integration.py          # Integration tests (250 lines, 17 tests)
├── .env.example                     # Environment template (95 lines)
├── .gitignore                       # Git exclusions (updated)
├── docker-compose.yml               # 4 services (MQTT, Prometheus, Grafana, nodes)
├── Dockerfile.iot-node              # IoT simulator container
├── LICENSE                          # MIT License
├── PROGRESS.md                      # Implementation tracking (540 lines)
├── QUICKSTART.md                    # Quick start guide
├── README.md                        # Main documentation (630+ lines)
├── requirements.txt                 # Python dependencies (15 packages)
├── SETUP.md                         # Setup instructions
└── task.md                          # Task tracking (Dev/Prod split)
```

## Core Components (1,680 lines of production code)

### 1. Intent Layer (294 lines)
- **api.py** (165 lines): Flask REST API with 5 endpoints
  - `POST /intents` - Submit new intent
  - `GET /intents` - List all intents
  - `GET /policies` - View active policies
  - `GET /health` - Health check
  - `POST /feedback` - Manual feedback trigger
- **parser.py** (129 lines): Regex-based NLP parser
  - 7 intent types: priority, bandwidth, latency, qos, reliability, power_saving, security
  - 30+ regex patterns for natural language

### 2. Policy Engine (214 lines)
- **engine.py**: Intent → Policy translation
  - Generates 5 policy types: tc_commands, mqtt_configs, routing_rules, iptables_rules, custom_actions
  - Uses YAML templates from `config/policy_templates.yaml`
  - Policy dataclass: `{id, intent_id, type, parameters, status, created_at}`

### 3. Enforcement Layer (399 lines)
- **network.py** (211 lines): Linux traffic control wrapper
  - `tc htb` for hierarchical bandwidth shaping
  - `tc netem` for latency/jitter injection
  - `iptables` for firewall rules
  - **Requires Linux** - fails gracefully on Windows
- **device.py** (188 lines): MQTT device control
  - Publishes to: `imperium/devices/{device_id}/config`
  - Subscribes to: `imperium/devices/{device_id}/telemetry`
  - QoS level configuration

### 4. Feedback Loop (280 lines)
- **monitor.py**: Closed-loop adaptation
  - Prometheus query integration
  - Metrics: `ibs_intent_satisfaction_ratio`, `ibs_policy_enforcement_latency_seconds`
  - Auto-adjustment when metrics deviate from intent targets
  - Convergence target: <2 minutes

### 5. IoT Simulator (184 lines)
- **node.py**: Dockerized IoT node
  - MQTT pub/sub for device telemetry
  - Configurable traffic patterns
  - Scalable via docker-compose (tested with 10+ nodes)

### 6. Main Controller (313 lines)
- **main.py**: System orchestrator
  - `ImperiumController` class
  - Components: IntentManager, PolicyEngine, NetworkEnforcer, DeviceEnforcer, FeedbackEngine
  - Methods: `initialize_components()`, `start_feedback_loop()`, `start_api_server()`

## Configuration Files (795 lines)

### devices.yaml (215 lines)
- 6 registered devices: temp-01, temp-02, camera-01, gateway-01, sensor-A, motion-01
- Device properties: `id, type, ip, priority, qos, bandwidth_limit, metadata`
- QoS profiles: 0 (at most once), 1 (at least once), 2 (exactly once)

### intent_grammar.yaml (250 lines)
- 7 intent categories with regex patterns
- Example: `"prioritize temperature sensors"` → `{"type": "priority", "targets": ["temp-*"]}`
- Handles complex intents: `"limit cameras to 100KB/s and reduce latency for sensors"`

### policy_templates.yaml (330 lines)
- 20+ tc command templates
- HTB qdisc templates: `tc qdisc add dev {interface} root handle 1: htb default 10`
- netem latency: `tc qdisc add dev {interface} parent 1:10 handle 10: netem delay {latency}ms`
- iptables rate limiting: `iptables -A FORWARD -s {ip} -m limit --limit {rate}/sec -j ACCEPT`

## Testing Suite (362 lines)

### test_core.py (112 lines)
- Unit tests for individual components
- Intent parser validation
- Policy generation logic

### test_integration.py (250 lines)
- 17 end-to-end integration tests
- Test scenarios:
  - Intent submission → policy generation
  - MQTT round-trip communication
  - Prometheus metrics collection
  - Feedback loop triggering
- Coverage: >60%

## Docker Infrastructure

### docker-compose.yml
```yaml
services:
  mosquitto:    # MQTT broker (ports 1883, 9001)
  prometheus:   # Metrics storage (port 9090, 5s scrape)
  grafana:      # Visualization (port 3000, admin/admin)
  iot-node:     # Scalable simulators
```

### Dockerfile.iot-node
- Python 3.9 base
- paho-mqtt client
- MQTT connection to broker
- Telemetry generation

## Python Dependencies (42 installed packages)

### Core (requirements.txt - 15 packages)
```
Flask==3.0.0           # REST API framework
paho-mqtt==1.6.1       # MQTT client
prometheus-client==0.19.0  # Metrics export
pandas==2.1.4          # Data processing
numpy==1.26.2          # Numerical operations
scapy==2.5.0           # Packet manipulation
netifaces==0.11.0      # Network interface detection
pytest==7.4.3          # Testing framework
pytest-cov==4.1.0      # Coverage reporting
pytest-asyncio==0.21.1 # Async testing
PyYAML==6.0.1          # YAML parsing
requests==2.31.0       # HTTP client
python-dotenv==1.0.0   # Environment variables
werkzeug==3.0.1        # WSGI utilities
nltk==3.8.1            # Natural language processing
```

### Full Environment (42 packages)
- Flask ecosystem: Werkzeug, Jinja2, Click, MarkupSafe, itsdangerous, Blinker
- Testing: pytest, pytest-cov, pytest-asyncio, pluggy, iniconfig
- Data: pandas, numpy, pytz, tzdata, python-dateutil, six
- Networking: scapy, netifaces, requests, urllib3, certifi, charset-normalizer, idna
- Others: PyYAML, python-dotenv, prometheus-client, paho-mqtt, nltk, regex, click, joblib

## Git Repository Status

### Tracked Files (After Cleanup)
- All source code modules (8 Python files in src/)
- Configuration files (3 YAML files)
- Tests (2 Python files)
- Docker infrastructure (1 compose file, 1 Dockerfile)
- Documentation (README, PROGRESS, SETUP, QUICKSTART, LICENSE, task.md)
- Environment template (.env.example)
- Grafana dashboards (3 JSON files)
- Git configuration (.gitignore)

### Excluded from Repository (.gitignore)
```
# Python artifacts
__pycache__/, *.pyc, *.egg-info/, build/, dist/

# Virtual environments
venv/, .venv/, ENV/, env/

# IDE files
.vscode/, .idea/, *.swp

# Logs
*.log, logs/

# Docker overrides
docker-compose.override.yml

# Monitoring data (runtime)
monitoring/prometheus/data/
monitoring/grafana/data/

# Sensitive configs
config/secrets.yml, config/*.secret

# OS files
.DS_Store, Thumbs.db

# Development utilities (Windows-specific)
*.bat                  # setup.bat, start_setup.bat, etc.
setup_structure.py     # Project structure generator
deploy.py              # Deployment helper

# Optional: Development tracking
# task.md
```

## Implementation Status

### ✅ Completed (95%)

#### Windows Development Environment
- [x] Python 3.11.9 virtual environment
- [x] 42 packages installed
- [x] Docker Compose services (MQTT, Prometheus, Grafana, IoT nodes)
- [x] All core modules implemented (1,680 lines)
- [x] Configuration files (795 lines)
- [x] Testing suite (362 lines, >60% coverage)
- [x] Documentation (630+ lines README, PROGRESS, SETUP)
- [x] Grafana dashboards (2 dashboards, 17 panels)
- [x] Git repository cleaned up (.gitignore updated)

#### Code Completeness
- [x] Intent Manager (Flask API + Regex parser)
- [x] Policy Engine (Intent → Policy translation)
- [x] Network Enforcement (tc/netem/iptables wrappers - logic complete)
- [x] Device Enforcement (MQTT publisher/subscriber)
- [x] Feedback Engine (Prometheus integration + auto-adjustment)
- [x] IoT Simulator (Dockerized, scalable)
- [x] Main Controller (Orchestration)

### ⏳ Pending (5%)

#### Raspberry Pi Production Deployment
- [ ] Hardware setup (Raspberry Pi 4 8GB RAM)
- [ ] Raspberry Pi OS 64-bit installation
- [ ] SSH configuration and network setup
- [ ] Real tc/iptables enforcement testing (Linux-only)
- [ ] Physical IoT device integration (ESP32)
- [ ] Security hardening (MQTT TLS, JWT auth)
- [ ] Persistence layer (SQLite/PostgreSQL)

#### Testing Validation
- [ ] Real bandwidth limiting on eth0
- [ ] Latency injection with netem
- [ ] Load testing with 50+ nodes
- [ ] Convergence time validation (<2 min target)

## Quick Start

### 1. Local Development (Windows)
```bash
# Clone repository
git clone https://github.com/Sonlux/Imperium.git
cd Imperium

# Setup virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start services
docker-compose up -d

# Run main controller
python src/main.py
```

### 2. Test API
```bash
# Submit intent
curl -X POST http://localhost:8000/intents \
  -H "Content-Type: application/json" \
  -d '{"intent": "prioritize temperature sensors"}'

# Check Grafana
Open: http://localhost:3000 (admin/admin)
```

### 3. Run Tests
```bash
pytest tests/ -v --cov=src --cov-report=html
```

## Performance Metrics

### Targets
- Policy enforcement latency: <500ms
- Feedback loop convergence: <2 minutes
- System resource usage: <60% CPU on Raspberry Pi
- Memory per process: <500MB

### Achieved (Simulated)
- Intent parsing: ~50ms
- Policy generation: ~100ms
- MQTT publish: ~20ms
- Prometheus scrape: 5s interval

## Security Considerations

### Current (Development)
- No authentication on REST API
- Plain MQTT (no TLS)
- No secrets encryption

### Planned (Production)
- [ ] JWT authentication for API
- [ ] MQTT TLS on port 8883
- [ ] API rate limiting
- [ ] SSH key-only authentication
- [ ] Firewall rules (ufw)

## Key Technologies

- **Python 3.11.9**: Primary language
- **Flask 3.0.0**: REST API framework
- **paho-mqtt 1.6.1**: MQTT client
- **Prometheus**: Metrics storage
- **Grafana**: Visualization
- **Docker**: Service orchestration
- **Linux tc/htb/netem**: Traffic control (Raspberry Pi only)
- **MQTT (Mosquitto)**: IoT messaging
- **Raspberry Pi OS 64-bit**: Target platform

## Resources

- **Repository**: https://github.com/Sonlux/Imperium
- **Linux tc man pages**: https://man7.org/linux/man-pages/man8/tc.8.html
- **MQTT Paho**: https://www.eclipse.org/paho/clients/python/
- **Prometheus Client**: https://github.com/prometheus/client_python

## Contact & Contribution

- Implementation by: Sonlux
- License: MIT
- Status: Active Development
- Next Milestone: Raspberry Pi deployment and real-world testing

---

**Last Updated:** 2025-01-01  
**Total Lines of Code:** 3,047 (source + config + tests)  
**Implementation Status:** 95% Complete  
**Ready for:** Raspberry Pi deployment
