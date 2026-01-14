# Project Tasks: Cognitive Edge-Orchestrated IBN

## Development Environment (Windows PC)

### Phase 1: Local Development Setup

- [x] **Dev Environment Configuration** <!-- id: dev-1 -->
  - [x] Install Python 3.9+, pip, virtualenv
  - [x] Install Docker Desktop for Windows
  - [x] Install VS Code with Remote-SSH extension
  - [x] Clone repository and setup virtual environment
- [x] **Local Service Stack** <!-- id: dev-2 -->
  - [x] Configure docker-compose.yml (MQTT, Prometheus, Grafana)
  - [x] Start local MQTT broker (port 1883)
  - [x] Start Prometheus (port 9090)
  - [x] Start Grafana (port 3000)
  - [x] Verify all services accessible from localhost

### Phase 2: Code Development & Testing

- [x] **Core Modules Implementation** <!-- id: dev-3 -->

  - [x] Intent Manager API (Flask REST endpoints)
  - [x] Intent Parser (regex/NLP-based)
  - [x] Policy Engine (intent → policy translation)
  - [x] Network Enforcement Module (tc wrapper - logic only)
  - [x] Device Enforcement Module (MQTT publisher)
  - [x] Feedback Engine (Prometheus integration)

- [x] **Configuration Files** <!-- id: dev-4 -->

  - [x] Create config/devices.yaml (device registry)
  - [x] Create config/intent_grammar.yaml (NLP patterns)
  - [x] Create config/policy_templates.yaml (tc templates)
  - [x] Create .env.example (environment template)

- [x] **Testing Suite** <!-- id: dev-5 -->
  - [x] Unit tests (test_core.py)
  - [x] Integration tests (test_integration.py)
  - [x] Run tests with pytest
  - [x] Verify code coverage (>60%)

### Phase 3: Simulation & Validation

- [x] **IoT Simulator** <!-- id: dev-6 -->

  - [x] Create Dockerized node simulator
  - [x] Implement MQTT pub/sub in simulator
  - [x] Scale simulator to 10+ nodes
  - [x] Generate realistic traffic patterns

- [x] **End-to-End Testing (Simulated)** <!-- id: dev-7 -->

  - [x] Submit intents via API
  - [x] Verify policy generation
  - [x] Verify MQTT commands sent to simulators
  - [x] Check Prometheus metrics collection
  - [x] Validate Grafana dashboard displays

- [x] **Windows-Specific Validation** <!-- id: dev-8 -->
  - [x] Test API endpoints (curl/Postman)
  - [x] Verify intent parsing accuracy
  - [x] Test MQTT device communication
  - [x] Monitor Grafana dashboards
  - [x] Run full integration test suite
  - [x] Document any Windows-specific issues

**Windows Validation Notes:**

- All API endpoints responding with 200 OK
- Intent parsing working correctly (7 intent types)
- MQTT broker connected and operational
- Grafana accessible at http://localhost:3000
- Docker services running (MQTT, Prometheus, Grafana, IoT nodes)
- **Known Limitation:** Network enforcement (tc/iptables) simulated on Windows - requires Linux for real enforcement

---

## Production Environment (Raspberry Pi 4 - Linux)

### Phase 1: Pi Initial Setup

- [x] **Hardware Connection** <!-- id: prod-1 -->

  - [x] Connect Pi to router via Ethernet (or direct to PC)
  - [x] Boot Raspberry Pi OS (64-bit recommended)
  - [x] Enable SSH (via raspi-config)
  - [x] Configure static IP or mDNS (raspberrypi.local)
  - [x] Test SSH connection from Windows PC

- [x] **System Preparation** <!-- id: prod-2 -->
  - [x] Update system: `sudo apt update && sudo apt upgrade -y`
  - [x] Install Python 3.9+: `sudo apt install python3 python3-pip python3-venv`
  - [x] Install Docker: `sudo apt install docker.io docker-compose`
  - [x] Install network tools: `sudo apt install iproute2 iptables` (verify present)
  - [x] Add pi user to docker group: `sudo usermod -aG docker pi`
  - [x] Verify `tc` command available: `tc -Version`

### Phase 2: Deployment

- [x] **Code Deployment** <!-- id: prod-3 -->

  - [x] Clone repository: `git clone https://github.com/Sonlux/Imperium.git`
  - [x] Create virtual environment: `python3 -m venv venv`
  - [x] Install dependencies: `pip install -r requirements.txt`
  - [x] Configure .env file (set NETWORK_INTERFACE=eth0)
  - [x] Set proper file permissions

- [x] **Service Stack Deployment** <!-- id: prod-4 -->
  - [x] Start docker-compose services
  - [x] Verify MQTT broker running
  - [x] Verify Prometheus scraping
  - [x] Verify Grafana accessible from Windows browser
  - [x] Check all containers healthy

### Phase 3: Network Enforcement Testing

- [x] **Linux-Specific Validation** <!-- id: prod-5 -->

  - [x] Test `tc` command execution (verify no permission errors)
  - [x] Apply test HTB qdisc: `sudo tc qdisc add dev eth0 root handle 1: htb`
  - [x] Verify network interface detection
  - [x] Test bandwidth limiting on real interface
  - [x] Test latency injection with netem
  - [x] Clean up test rules: `sudo tc qdisc del dev eth0 root`

- [x] **Real-World Policy Enforcement** <!-- id: prod-6 -->
  - [x] Submit intent via API from Windows PC
  - [x] Verify tc commands executed successfully
  - [x] Monitor network traffic with `iftop` or `nethogs`
  - [x] Verify bandwidth limits applied
  - [x] Test latency changes with ping
  - [x] Validate iptables rules if used

### Phase 4: IoT Node Integration

- [ ] **Physical IoT Devices** <!-- id: prod-7 -->

  - [ ] Connect ESP32/physical IoT nodes to network
  - [ ] Configure nodes to connect to Pi's MQTT broker
  - [ ] Verify nodes receive policy updates
  - [ ] Test QoS level changes
  - [ ] Test sampling rate adjustments
  - [ ] Monitor device telemetry in Grafana

- [ ] **Hybrid Testing** <!-- id: prod-8 -->
  - [ ] Run mix of physical + simulated nodes
  - [ ] Apply different policies to each type
  - [ ] Verify isolation between device groups
  - [ ] Test priority-based traffic shaping
  - [ ] Measure actual latency improvements

### Phase 5: Feedback Loop Validation

- [ ] **Closed-Loop Testing** <!-- id: prod-9 -->

  - [ ] Submit intent with specific latency target
  - [ ] Monitor Prometheus metrics collection
  - [ ] Verify feedback engine detects violations
  - [ ] Test automatic policy adjustments
  - [ ] Measure convergence time (<2 minutes target)
  - [ ] Validate stability (no oscillation)

- [ ] **Load Testing** <!-- id: prod-10 -->
  - [ ] Scale to 50+ IoT nodes (simulated + real)
  - [ ] Submit multiple conflicting intents
  - [ ] Monitor Pi CPU/memory usage (<60% target)
  - [ ] Test policy enforcement latency (<500ms)
  - [ ] Verify system stability under load
  - [ ] Document performance bottlenecks

### Phase 6: Production Hardening

- [ ] **Security** <!-- id: prod-11 -->

  - [ ] Enable MQTT TLS (port 8883)
  - [x] Configure JWT authentication for API
  - [x] Setup API rate limiting
  - [ ] Configure firewall rules (ufw)
  - [ ] Disable default passwords
  - [ ] Setup SSH key-only authentication

- [x] **Persistence & Reliability** <!-- id: prod-12 -->
  - [x] Add SQLite/PostgreSQL for intent history
  - [x] Implement systemd service for auto-start
  - [ ] Configure log rotation
  - [ ] Setup backup mechanism for configs
  - [ ] Test recovery from crashes
  - [ ] Document disaster recovery procedures

---

## Summary

**Development (Windows):** ✅ 95% Complete  
**Production (Raspberry Pi):** ✅ 80% Complete - Core deployment successful!

**Completed on 2026-01-14:**
1. ✅ Pi Initial Setup (prod-1, prod-2)
2. ✅ Code Deployment (prod-3)
3. ✅ Service Stack Deployment (prod-4)
4. ✅ Network Enforcement Testing (prod-5, prod-6)
5. ✅ Systemd service configured and enabled (prod-12)

**Testing Verified:**
- ✅ Health endpoint: 200 OK
- ✅ JWT authentication: Working
- ✅ Intent submission: Policies generated successfully
- ✅ TC commands: HTB qdisc/class creation verified
- ✅ Docker services: MQTT, Prometheus, Grafana running
- ✅ Database: SQLite with admin user initialized

**Remaining Tasks:**
- [ ] prod-7: Physical IoT device integration
- [ ] prod-8: Hybrid testing (physical + simulated nodes)
- [ ] prod-9: Closed-loop testing
- [ ] prod-10: Load testing (50+ nodes)
- [ ] prod-11: Security hardening (TLS, firewall)
2. Setup Raspberry Pi hardware (Phase 1, prod-1 & prod-2)
3. Deploy to Pi and test network enforcement (Phase 3, prod-5 & prod-6)
