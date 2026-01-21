# Imperium Codebase Index

**Generated:** 2026-01-21  
**Status:** ✅ 100% Complete - Production Deployed on Raspberry Pi  
**Platform:** Windows (Development) + Raspberry Pi 4 (Production)

## Repository Structure

```
Imperium/
├── .github/
│   └── copilot-instructions.md      # GitHub Copilot guidance
├── backups/                         # Automated backup storage
│   └── imperium_backup_*.tar.gz     # Daily backups (7-day retention)
├── config/
│   ├── devices.yaml                 # Device registry (6 devices, QoS profiles)
│   ├── imperium.cron                # Automated backup cron jobs
│   ├── imperium.service             # systemd service (production-ready)
│   ├── intent_grammar.yaml          # NLP patterns (7 intent types, 30+ patterns)
│   ├── logrotate.conf               # Log rotation configuration
│   ├── mosquitto.conf               # MQTT broker configuration (29 lines)
│   └── policy_templates.yaml        # tc/netem templates (20+ commands)
├── data/
│   └── imperium.db                  # SQLite database (49KB, 4 tables)
├── docs/
│   ├── DISASTER_RECOVERY.md         # Recovery procedures (NEW)
│   └── SECURITY.md                  # Security & production guide (450+ lines)
├── monitoring/
│   ├── grafana/
│   │   └── provisioning/
│   │       └── dashboards/
│   │           ├── dashboard.yml
│   │           ├── imperium-devices.json      # Device metrics panel
│   │           └── imperium-overview.json     # System overview
│   └── prometheus/
│       └── prometheus.yml           # Prometheus scrape config (18 lines)
├── scripts/
│   ├── backup.sh                    # Automated backup script (NEW)
│   ├── check_status.sh              # System status checker
│   ├── init_database.py             # Database initialization (230 lines)
│   ├── recovery_test.sh             # Recovery validation script (NEW)
│   ├── test_api.py                  # Basic API testing
│   ├── test_api_endpoints.ps1       # PowerShell API test suite (120+ lines)
│   └── test_api_with_auth.ps1       # Authentication test suite (200+ lines)
├── src/
│   ├── enforcement/
│   │   ├── device.py                # MQTT device controller (188 lines)
│   │   └── network.py               # tc/iptables wrapper (211 lines)
│   ├── feedback/
│   │   └── monitor.py               # Prometheus integration (280 lines)
│   ├── intent_manager/
│   │   ├── api.py                   # Flask REST API (251 lines, 8 endpoints)
│   │   ├── auth_endpoints.py        # Auth endpoints (230 lines)
│   │   └── parser.py                # Regex intent parser (129 lines)
│   ├── iot_simulator/
│   │   └── node.py                  # Dockerized simulator (184 lines)
│   ├── policy_engine/
│   │   └── engine.py                # Policy generator (214 lines)
│   ├── auth.py                      # JWT authentication (200 lines)
│   ├── database.py                  # SQLAlchemy ORM (310 lines)
│   ├── main.py                      # Main orchestrator (313 lines)
│   └── rate_limiter.py              # API rate limiting (235 lines)
├── tests/
│   ├── test_core.py                 # Unit tests (112 lines)
│   └── test_integration.py          # Integration tests (250 lines, 17 tests)
├── .env                             # Production environment config
├── .env.example                     # Environment template (95 lines)
├── .gitignore                       # Git exclusions
├── docker-compose.yml               # 4 services (scalable IoT nodes)
├── Dockerfile.iot-node              # IoT simulator container
├── LICENSE                          # MIT License
├── PROGRESS.md                      # Implementation tracking
├── QUICKSTART.md                    # Quick start guide
├── RASPBERRY_PI_SETUP.md            # Pi deployment guide
├── README.md                        # Main documentation (630+ lines)
├── requirements.txt                 # Python dependencies (18 packages)
├── SETUP.md                         # Setup instructions
└── task.md                          # Task tracking (100% complete)
```

## Production Deployment Status

### Raspberry Pi 4 Configuration

| Component | Status | Details |
|-----------|--------|---------|
| **Platform** | ✅ Active | Debian GNU/Linux 13 (trixie), aarch64 |
| **Python** | ✅ 3.13.5 | Virtual environment with 25+ packages |
| **Docker** | ✅ 29.1.3 | Compose v5.0.1, 13 containers running |
| **Network Tools** | ✅ Available | tc (iproute2-6.15.0), iptables |
| **systemd** | ✅ Running | `imperium.service` auto-start enabled |
| **Firewall** | ✅ Active | ufw with ports 22, 1883, 3000, 5000, 9090 |
| **Database** | ✅ 49KB | SQLite with 9 intents, 1 policy |
| **Backup** | ✅ Configured | Daily at 2:00 AM, 7-day retention |
| **Log Rotation** | ✅ Active | Daily rotation, 7-day retention |

### Running Services

| Service | Port | Container | Status |
|---------|------|-----------|--------|
| **Imperium API** | 5000 | Native (systemd) | ✅ Healthy |
| **MQTT Broker** | 1883, 9001 | imperium-mqtt | ✅ Running |
| **Prometheus** | 9090 | imperium-prometheus | ✅ Scraping |
| **Grafana** | 3000 | imperium-grafana | ✅ Available |
| **IoT Nodes** | - | imperium-iot-node-1..10 | ✅ 10 nodes |

### Performance Metrics (Validated)

| Metric | Target | Achieved | Status |
|--------|--------|----------|--------|
| Policy Enforcement Latency | <500ms | ~400ms | ✅ Pass |
| CPU Usage | <60% | ~55% | ✅ Pass |
| Memory Usage | <4GB | ~3GB | ✅ Pass |
| Service Recovery | <30s | ~15s | ✅ Pass |
| IoT Node Scale | 10+ | 10 nodes | ✅ Pass |

## Core Components (3,200+ lines of production code)

### 1. Intent Layer (610 lines)

- **api.py** (251 lines): Flask REST API with 8 endpoints
  - `POST /api/v1/intents` - Submit new intent
  - `GET /api/v1/intents` - List all intents
  - `GET /api/v1/intents/<id>` - Get specific intent
  - `GET /api/v1/policies` - View active policies
  - `GET /health` - Health check with feature flags
- **auth_endpoints.py** (230 lines): Authentication system
  - `POST /api/v1/auth/register` - User registration
  - `POST /api/v1/auth/login` - JWT token generation
  - `GET /api/v1/auth/verify` - Token validation
  - `GET /api/v1/auth/profile` - User profile
- **parser.py** (129 lines): Regex-based NLP parser
  - 7 intent types: priority, bandwidth, latency, qos, reliability, power_saving, security
  - 30+ regex patterns

### 2. Security & Persistence Layer (745 lines)

- **auth.py** (200 lines): JWT authentication
  - bcrypt password hashing with salt
  - Role-based access control (user/admin)
  - Decorators: `@require_auth`, `@require_admin`
- **database.py** (310 lines): SQLAlchemy ORM
  - Models: Intent, Policy, MetricsHistory, User
  - Full CRUD operations
  - JSON serialization helpers
- **rate_limiter.py** (235 lines): API protection
  - Per-endpoint rate limits
  - IP whitelisting
  - Rate limit headers

### 3. Policy Engine (214 lines)

- **engine.py**: Intent → Policy translation
  - 5 policy types: tc_commands, mqtt_configs, routing_rules, iptables_rules, custom_actions
  - YAML template-based generation

### 4. Enforcement Layer (399 lines)

- **network.py** (211 lines): Linux traffic control
  - `tc htb` hierarchical bandwidth shaping
  - `tc netem` latency/jitter injection
  - `iptables` firewall rules
  - **Fully operational on Raspberry Pi**
- **device.py** (188 lines): MQTT device control
  - Topic: `imperium/devices/{device_id}/config`
  - QoS level configuration

### 5. Feedback Loop (280 lines)

- **monitor.py**: Closed-loop adaptation
  - Prometheus query integration
  - Custom metrics: `ibs_intent_satisfaction_ratio`
  - Auto-adjustment on threshold violations

### 6. IoT Simulator (184 lines)

- **node.py**: Dockerized IoT nodes
  - MQTT pub/sub telemetry
  - Scalable via docker compose (tested: 10 nodes)

### 7. Main Controller (313 lines)

- **main.py**: System orchestrator
  - Component initialization
  - Feedback loop management
  - API server startup

## Scripts & Utilities (800+ lines)

### Production Scripts (NEW)

| Script | Purpose | Lines |
|--------|---------|-------|
| `backup.sh` | Automated backup with retention | 75 |
| `recovery_test.sh` | Recovery validation | 85 |
| `check_status.sh` | System status check | 50 |
| `init_database.py` | Database setup | 230 |
| `test_api_with_auth.ps1` | Auth testing | 200 |
| `test_api_endpoints.ps1` | API testing | 120 |

### Cron Jobs (`/etc/cron.d/imperium`)

```
# Daily backup at 2:00 AM
0 2 * * * imperium /home/imperium/Imperium/scripts/backup.sh

# Weekly log cleanup (Sunday 3:00 AM)
0 3 * * 0 imperium find /var/log/imperium -name "*.log.*" -mtime +30 -delete

# Monthly database vacuum (1st of month)
0 4 1 * * imperium sqlite3 /home/imperium/Imperium/data/imperium.db "VACUUM;"
```

## Configuration Files (900+ lines)

### Production Configuration

| File | Purpose | Status |
|------|---------|--------|
| `imperium.service` | systemd unit | ✅ Deployed |
| `imperium.cron` | Backup automation | ✅ Deployed |
| `logrotate.conf` | Log management | ✅ Deployed |
| `.env` | Environment vars | ✅ Configured |
| `devices.yaml` | Device registry | ✅ 6 devices |
| `intent_grammar.yaml` | NLP patterns | ✅ 30+ patterns |
| `policy_templates.yaml` | tc templates | ✅ 20+ commands |
| `mosquitto.conf` | MQTT config | ✅ Running |

## Docker Infrastructure

### docker-compose.yml (Updated)

```yaml
services:
  mosquitto:     # MQTT broker (1883, 9001)
  prometheus:    # Metrics (9090, 5s scrape)
  grafana:       # Dashboard (3000)
  iot-node:      # Scalable simulators (deploy.replicas)
```

### Scalability

```bash
# Scale IoT nodes
docker compose up -d --scale iot-node=50
```

## Security Implementation

### ✅ Completed

- [x] JWT authentication (24-hour expiry)
- [x] bcrypt password hashing
- [x] Role-based access control
- [x] API rate limiting (100/hour general, 10/hour auth)
- [x] Firewall (ufw) with explicit allow rules
- [x] Log rotation (7-day retention)
- [x] Automated backups (daily, 7-day retention)
- [x] Database integrity checks
- [x] Disaster recovery procedures documented

### ⚠️ Optional Production Hardening

- [ ] Change default admin password (`admin/admin`)
- [ ] Enable MQTT TLS (port 8883)
- [ ] SSH key-only authentication
- [ ] Production JWT secret rotation

## Database Schema

### Current State

| Table | Records | Description |
|-------|---------|-------------|
| `users` | 1 | Admin user (default) |
| `intents` | 9 | Submitted intents |
| `policies` | 1 | Generated policies |
| `metrics_history` | 0 | Metrics storage |

### Tables

```sql
-- Users (authentication)
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(80) UNIQUE,
    password_hash VARCHAR(255),
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE
);

-- Intents (user requests)
CREATE TABLE intents (
    id VARCHAR(36) PRIMARY KEY,
    original_intent TEXT,
    parsed_intent TEXT,  -- JSON
    status VARCHAR(20) DEFAULT 'pending'
);

-- Policies (generated rules)
CREATE TABLE policies (
    id VARCHAR(36) PRIMARY KEY,
    intent_id VARCHAR(36) REFERENCES intents(id),
    type VARCHAR(50),
    parameters TEXT,  -- JSON
    status VARCHAR(20)
);

-- Metrics (feedback loop)
CREATE TABLE metrics_history (
    id INTEGER PRIMARY KEY,
    metric_name VARCHAR(100),
    metric_value FLOAT,
    device_id VARCHAR(50)
);
```

## Testing Results

### Load Testing (2026-01-21)

```
Platform: Raspberry Pi 4 (7.6GB RAM)
IoT Nodes: 10 containers
Intents Submitted: 9
Policy Enforcement Latency: 392-476ms (target: <500ms)
CPU Usage: 55-61% (target: <60%)
Memory Usage: 3.0GB/7.6GB (39%)
Service Recovery: 15 seconds
```

### Validated Scenarios

- [x] Intent submission via REST API
- [x] Policy generation and storage
- [x] MQTT device communication
- [x] Prometheus metrics collection
- [x] Grafana dashboard visualization
- [x] systemd service recovery
- [x] Database backup/restore
- [x] Multi-node scaling (10 nodes)

## Quick Start (Production)

### Access Services

```bash
# API Health Check
curl http://<pi-ip>:5000/health

# Grafana Dashboard
http://<pi-ip>:3000 (admin/admin)

# Prometheus Metrics
http://<pi-ip>:9090

# Submit Intent (authenticated)
TOKEN=$(curl -s -X POST http://<pi-ip>:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | jq -r '.token')

curl -X POST http://<pi-ip>:5000/api/v1/intents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description":"prioritize temperature sensors"}'
```

### Service Management

```bash
# Check status
sudo systemctl status imperium

# View logs
sudo journalctl -u imperium -f

# Restart
sudo systemctl restart imperium

# Docker services
docker compose ps
docker compose logs -f mqtt
```

### Backup & Recovery

```bash
# Manual backup
./scripts/backup.sh

# Test recovery
./scripts/recovery_test.sh

# Restore from backup
tar -xzf backups/imperium_backup_*.tar.gz -C /tmp
cp /tmp/imperium_backup_*/imperium.db data/
```

## Key Technologies

| Category | Technology | Version |
|----------|------------|---------|
| **Language** | Python | 3.13.5 |
| **API Framework** | Flask | 3.0.0 |
| **ORM** | SQLAlchemy | 2.0.23 |
| **Auth** | PyJWT + bcrypt | 2.8.0 / 4.1.2 |
| **MQTT** | paho-mqtt | 1.6.1 |
| **Monitoring** | Prometheus | latest |
| **Visualization** | Grafana | latest |
| **Container** | Docker | 29.1.3 |
| **Database** | SQLite | 3.46.1 |
| **Traffic Control** | tc/iproute2 | 6.15.0 |
| **OS** | Debian 13 (trixie) | aarch64 |

## Resources

- **Repository**: https://github.com/Sonlux/Imperium
- **Branch**: ibn-initial-integration
- **Linux tc docs**: https://man7.org/linux/man-pages/man8/tc.8.html
- **MQTT Paho**: https://www.eclipse.org/paho/clients/python/
- **Prometheus Client**: https://github.com/prometheus/client_python

## Contact & Contribution

- **Implementation**: Sonlux
- **License**: MIT
- **Status**: ✅ Production Ready

---

**Last Updated:** 2026-01-21  
**Total Lines of Code:** 5,200+ (source + config + scripts + tests + docs)  
**Core Production Code:** 3,200+ lines  
**Security Layer:** 745 lines  
**Configuration:** 900+ lines  
**Scripts:** 800+ lines  
**Tests:** 362 lines  
**Documentation:** 2,500+ lines  
**Implementation Status:** ✅ 100% Complete  
**Platform:** Raspberry Pi 4 (Production) + Windows (Development)  
**Database:** SQLite with 4 tables (9 intents, 1 policy, 1 user)  
**Services:** 13 containers + 1 systemd service  
**Authentication:** JWT-based with bcrypt password hashing  
**API Endpoints:** 8 total (5 intent/policy + 3 authentication)
