# Imperium Codebase Index

**Generated:** 2026-01-03  
**Status:** 100% Core Complete + Security Features Implemented  
**Platform:** Windows (Development) → Raspberry Pi (Production)

## Repository Structure

```
Imperium/
├── .github/
│   └── copilot-instructions.md      # GitHub Copilot guidance
├── config/
│   ├── devices.yaml                 # Device registry (6 devices, QoS profiles)
│   ├── imperium.service             # systemd service template for Linux
│   ├── intent_grammar.yaml          # NLP patterns (7 intent types, 30+ patterns)
│   ├── mosquitto.conf               # MQTT broker configuration (29 lines)
│   └── policy_templates.yaml        # tc/netem templates (20+ commands)
├── data/
│   └── imperium.db                  # SQLite database (persistent storage)
├── docs/
│   └── SECURITY.md                  # Security & production features guide (450+ lines)
├── monitoring/
│   ├── grafana/
│   │   └── provisioning/
│   │       └── dashboards/
│   │           ├── dashboard.yml
│   │           ├── imperium-dev-dashboard.json     # 17 panels
│   │           └── imperium-overview.json          # System overview
│   └── prometheus/
│       └── prometheus.yml           # Prometheus scrape configuration (18 lines)
├── scripts/
│   ├── init_database.py             # Database initialization (230 lines)
│   ├── test_api.py                  # Basic API testing
│   ├── test_api_endpoints.ps1      # PowerShell API test suite (120+ lines)
│   └── test_api_with_auth.ps1      # Authentication test suite (200+ lines)
├── src/
│   ├── enforcement/
│   │   ├── device.py                # MQTT device controller (188 lines)
│   │   └── network.py               # tc/iptables wrapper (211 lines, Linux-only)
│   ├── feedback/
│   │   └── monitor.py               # Prometheus integration (280 lines)
│   ├── intent_manager/
│   │   ├── api.py                   # Flask REST API (251 lines, 5+ endpoints)
│   │   ├── auth_endpoints.py        # Authentication endpoints (230 lines)
│   │   └── parser.py                # Regex intent parser (129 lines)
│   ├── iot_simulator/
│   │   └── node.py                  # Dockerized simulator (184 lines)
│   ├── policy_engine/
│   │   └── engine.py                # Policy generator (214 lines)
│   ├── auth.py                      # JWT authentication system (200 lines)
│   ├── database.py                  # SQLAlchemy ORM models (310 lines)
│   ├── main.py                      # Main orchestrator (313 lines)
│   └── rate_limiter.py              # API rate limiting (235 lines)
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
├── requirements.txt                 # Python dependencies (18 packages)
├── SETUP.md                         # Setup instructions
└── task.md                          # Task tracking (Dev/Prod split, 203 lines)
```

## Core Components (2,925 lines of production code)

### 1. Intent Layer (610 lines)

- **api.py** (251 lines): Flask REST API with 8 endpoints
  - `POST /api/v1/intents` - Submit new intent
  - `GET /api/v1/intents` - List all intents
  - `GET /api/v1/intents/<id>` - Get specific intent
  - `GET /api/v1/policies` - View active policies
  - `GET /health` - Health check
  - Database and authentication integrated
- **auth_endpoints.py** (230 lines): User authentication system
  - `POST /api/v1/auth/register` - Register new user
  - `POST /api/v1/auth/login` - JWT authentication
  - `GET /api/v1/auth/verify` - Verify token
  - `GET /api/v1/auth/profile` - Get user profile
  - Input validation and error handling
- **parser.py** (129 lines): Regex-based NLP parser
  - 7 intent types: priority, bandwidth, latency, qos, reliability, power_saving, security
  - 30+ regex patterns for natural language

### 2. Security & Persistence Layer (745 lines)

- **auth.py** (200 lines): JWT authentication system
  - AuthManager class for token generation/validation
  - bcrypt password hashing
  - Role-based access control (user/admin)
  - Authentication decorators: `@require_auth`, `@require_admin`
  - Default admin user creation
- **database.py** (310 lines): SQLAlchemy ORM layer
  - Models: Intent, Policy, MetricsHistory, User
  - DatabaseManager with full CRUD operations
  - Relationship mapping (intents ↔ policies)
  - JSON serialization helpers
  - Session management
- **rate_limiter.py** (235 lines): API rate limiting
  - RateLimiter class with in-memory tracking
  - Configurable per-endpoint limits
  - IP whitelisting support
  - Rate limit statistics
  - Headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset

### 3. Policy Engine (214 lines)

- **engine.py**: Intent → Policy translation
  - Generates 5 policy types: tc_commands, mqtt_configs, routing_rules, iptables_rules, custom_actions
  - Uses YAML templates from `config/policy_templates.yaml`
  - Policy dataclass: `{id, intent_id, type, parameters, status, created_at}`

### 4. Enforcement Layer (399 lines)

- **network.py** (211 lines): Linux traffic control wrapper
  - `tc htb` for hierarchical bandwidth shaping
  - `tc netem` for latency/jitter injection
  - `iptables` for firewall rules
  - **Requires Linux** - simulated on Windows
- **device.py** (188 lines): MQTT device control
  - Publishes to: `imperium/devices/{device_id}/config`
  - Subscribes to: `imperium/devices/{device_id}/telemetry`
  - QoS level configuration

### 5. Feedback Loop (280 lines)

- **monitor.py**: Closed-loop adaptation
  - Prometheus query integration
  - Metrics: `ibs_intent_satisfaction_ratio`, `ibs_policy_enforcement_latency_seconds`
  - Auto-adjustment when metrics deviate from intent targets
  - Convergence target: <2 minutes

### 6. IoT Simulator (184 lines)

- **node.py**: Dockerized IoT node
  - MQTT pub/sub for device telemetry
  - Configurable traffic patterns
  - Scalable via docker-compose (tested with 10+ nodes)

### 7. Main Controller (313 lines)

- **main.py**: System orchestrator
  - `ImperiumController` class
  - Components: IntentManager, PolicyEngine, NetworkEnforcer, DeviceEnforcer, FeedbackEngine
  - Database and authentication initialization
  - Methods: `initialize_components()`, `start_feedback_loop()`, `start_api_server()`

## Configuration Files (825 lines)

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

### mosquitto.conf (29 lines)

- MQTT broker configuration for development
- Listener on port 1883 (MQTT) and 9001 (WebSocket)
- Anonymous authentication enabled (development only)
- Persistence enabled at `/mosquitto/data/`

### prometheus.yml (18 lines)

- Global scrape interval: 5 seconds
- 3 scrape jobs:
  - prometheus (localhost:9090)
  - imperium-controller (host.docker.internal:8000)
  - iot-nodes (iot-node-1:8001)

### imperium.service (52 lines)

- systemd service unit for Linux deployment
- Auto-restart on failure (max 3 attempts per 60s)
- Resource limits: 512MB RAM, 60% CPU
- Environment variables for JWT secret, database path
- Logging to `/var/log/imperium/`

## Scripts & Utilities (592 lines)

### init_database.py (230 lines)

- Database initialization and setup
- Creates all tables: intents, policies, metrics_history, users
- Creates default admin user (username: `admin`, password: `admin`)
- Includes verification tests
- Supports data migration from in-memory storage

### test_api.py (42 lines)

- Basic API testing utility
- Simple endpoint validation

### test_api_endpoints.ps1 (120 lines)

- PowerShell-based API test suite
- Tests 7 scenarios:
  1. Health check
  2. Priority intent submission
  3. Bandwidth intent submission
  4. Latency intent submission
  5. List all intents
  6. List all policies
  7. Get specific intent details
- Color-coded output (Green/Red/Yellow)
- Provides next steps after testing

### test_api_with_auth.ps1 (200 lines)

- Comprehensive authentication test suite
- 10 test phases:
  1. Public endpoints (health check)
  2. User registration
  3. Admin authentication
  4. Token verification
  5. User profile retrieval
  6. Unauthenticated intent submission
  7. Authenticated intent submission (3 intents)
  8. List intents with auth
  9. List policies with auth
  10. Rate limiting validation
- JWT token management
- Success/failure tracking with summary

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

## Documentation (1,850+ lines)

### README.md (630+ lines)

- Project overview and architecture
- Quick start guide
- Installation instructions
- API documentation
- Deployment guidelines

### SECURITY.md (450+ lines)

- **Authentication System**
  - JWT token-based authentication
  - User registration and login
  - Token verification
  - Password requirements
- **Rate Limiting**
  - Per-endpoint limits configuration
  - Rate limit headers
  - IP whitelisting
  - Statistics monitoring
- **Database Operations**
  - SQLite schema documentation
  - CRUD operations guide
  - Backup and recovery procedures
- **Deployment Guides**
  - Windows development setup
  - Raspberry Pi production deployment
  - systemd service configuration
  - Security best practices
- **Environment Configuration**
  - Required environment variables
  - .env file examples
  - JWT secret generation
- **Monitoring & Testing**
  - Authentication event logging
  - Rate limit statistics
  - Database metrics
  - Test suite execution

### PROGRESS.md (540 lines)

- Implementation timeline
- Completed features tracking
- Pending work identification

### QUICKSTART.md

- Quick setup guide
- Essential commands
- Common workflows

### SETUP.md

- Detailed setup instructions
- Dependency installation
- Configuration steps

### task.md (203 lines)

- Development environment tasks (8 phases)
- Production environment tasks (6 phases)
- Windows validation notes
- Raspberry Pi deployment checklist

## Docker Infrastructure

### docker-compose.yml

```yaml
services:
  mosquitto: # MQTT broker (ports 1883, 9001)
  prometheus: # Metrics storage (port 9090, 5s scrape)
  grafana: # Visualization (port 3000, admin/admin)
  iot-node: # Scalable simulators
```

### Dockerfile.iot-node

- Python 3.9 base
- paho-mqtt client
- MQTT connection to broker
- Telemetry generation

## Python Dependencies (18 packages + 42 total with transitive)

### Core (requirements.txt - 18 packages)

```
# Core Dependencies
Flask==3.0.0           # REST API framework
flask-cors==4.0.0      # CORS support
paho-mqtt==1.6.1       # MQTT client
prometheus-client==0.19.0  # Metrics export
pyyaml==6.0.1          # YAML parsing
requests==2.31.0       # HTTP client

# Security & Authentication
pyjwt==2.8.0           # JWT token handling
bcrypt==4.1.2          # Password hashing

# Database
sqlalchemy==2.0.23     # ORM

# Data Processing
pandas==2.1.4          # Data processing
numpy==1.26.2          # Numerical operations

# Networking Tools
scapy==2.5.0           # Packet manipulation
netifaces==0.11.0      # Network interface detection

# Testing
pytest==7.4.3          # Testing framework
pytest-cov==4.1.0      # Coverage reporting
pytest-mock==3.12.0    # Mock testing

# Development
black==23.12.1         # Code formatting
flake8==6.1.0          # Linting
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

### ✅ Completed (100% Core + Security Features)

#### Windows Development Environment

- [x] Python 3.11.9 virtual environment
- [x] 42 packages installed (18 direct + transitive dependencies)
- [x] Docker Compose services (MQTT, Prometheus, Grafana, IoT nodes)
- [x] All core modules implemented (2,925 lines)
- [x] Security features (745 lines): Auth, Database, Rate Limiting
- [x] Configuration files (825 lines)
- [x] Scripts and utilities (592 lines)
- [x] Testing suite (362 lines, >60% coverage)
- [x] Documentation (1,850+ lines)
- [x] Grafana dashboards (2 dashboards, 17 panels)
- [x] Git repository cleaned up (.gitignore updated)
- [x] **SQLite database initialized with admin user**
- [x] **JWT authentication system operational**
- [x] **API rate limiting configured**
- [x] **Authentication endpoints registered**
- [x] **Database persistence layer integrated**

#### Code Completeness

- [x] Intent Manager (Flask API + Regex parser)
- [x] Authentication System (JWT + bcrypt + role-based access)
- [x] Database Layer (SQLAlchemy ORM + migrations)
- [x] Rate Limiting (Per-endpoint + IP whitelist)
- [x] Policy Engine (Intent → Policy translation)
- [x] Network Enforcement (tc/netem/iptables wrappers - simulated on Windows)
- [x] Device Enforcement (MQTT publisher/subscriber)
- [x] Feedback Engine (Prometheus integration + auto-adjustment)
- [x] IoT Simulator (Dockerized, scalable)
- [x] Main Controller (Full orchestration with all features)

### ⏳ Pending (Raspberry Pi Deployment)

#### Hardware & Linux-Specific Testing

- [ ] Hardware setup (Raspberry Pi 4 8GB RAM)
- [ ] Raspberry Pi OS 64-bit installation
- [ ] SSH configuration and network setup
- [ ] Real tc/iptables enforcement testing (Linux-only)
- [ ] Physical IoT device integration (ESP32)
- [ ] Production security hardening (MQTT TLS, HTTPS)

#### Production Validation

- [ ] Real bandwidth limiting on eth0
- [ ] Latency injection with netem
- [ ] Load testing with 50+ nodes
- [ ] Convergence time validation (<2 min target)
- [ ] Resource usage validation on Pi hardware

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

# Initialize database
python scripts/init_database.py

# Start Docker services
docker-compose up -d

# Run main controller
python src/main.py
```

### 2. Test Authentication & API

```powershell
# Run comprehensive authentication test suite
.\scripts\test_api_with_auth.ps1

# Or test manually with PowerShell
$body = @{username='admin'; password='admin'} | ConvertTo-Json
$response = Invoke-RestMethod -Method POST `
    -Uri 'http://localhost:5000/api/v1/auth/login' `
    -Body $body -ContentType 'application/json'

# Use token for protected endpoints
$headers = @{Authorization = "Bearer $($response.token)"}
Invoke-RestMethod -Method POST -Uri 'http://localhost:5000/api/v1/intents' `
    -Headers $headers -Body '{"description":"prioritize sensors"}' `
    -ContentType 'application/json'
```

### 3. Monitor System

```bash
# Grafana Dashboard
http://localhost:3000 (admin/admin)

# Prometheus Metrics
http://localhost:9090

# API Health Check
http://localhost:5000/health

# Database
sqlite3 data/imperium.db
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

### Production-Ready Features ✅

- **JWT Authentication**: Token-based API authentication with 24-hour expiry
- **Password Security**: bcrypt hashing with salt
- **Rate Limiting**: Per-endpoint limits (100/hour general, 10/hour auth, 50/hour intents)
- **Database Persistence**: SQLite with SQLAlchemy ORM
- **Role-Based Access**: User and admin roles with decorator-based enforcement
- **Logging**: Comprehensive event logging for security monitoring

### Current (Development)

- Default admin credentials (username: `admin`, password: `admin`) - **Change in production!**
- Plain MQTT (no TLS) - Development only
- SQLite database - Suitable for single-Pi deployment
- No HTTPS - Use reverse proxy in production

### Planned (Production Hardening)

- [ ] Change default admin password
- [ ] MQTT TLS on port 8883
- [ ] HTTPS via nginx reverse proxy
- [ ] JWT secret key rotation
- [ ] SSH key-only authentication
- [ ] Firewall rules (ufw)
- [ ] Regular database backups
- [ ] Production-grade WSGI server (gunicorn/uwsgi)

## Key Technologies

- **Python 3.11.9**: Primary language
- **Flask 3.0.0**: REST API framework
- **SQLAlchemy 2.0.23**: ORM for database operations
- **PyJWT 2.8.0**: JWT token handling
- **bcrypt 4.1.2**: Password hashing
- **paho-mqtt 1.6.1**: MQTT client
- **Prometheus**: Metrics storage and monitoring
- **Grafana**: Visualization and dashboards
- **Docker**: Service orchestration and containerization
- **SQLite**: Persistent database storage
- **Linux tc/htb/netem**: Traffic control (Raspberry Pi only)
- **MQTT (Mosquitto)**: IoT messaging broker
- **Raspberry Pi OS 64-bit**: Target production platform

## Database Schema

### Intents Table

```sql
CREATE TABLE intents (
    id VARCHAR(36) PRIMARY KEY,
    original_intent TEXT NOT NULL,
    parsed_intent TEXT,              -- JSON
    status VARCHAR(20) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Policies Table

```sql
CREATE TABLE policies (
    id VARCHAR(36) PRIMARY KEY,
    intent_id VARCHAR(36) REFERENCES intents(id),
    type VARCHAR(50) NOT NULL,
    parameters TEXT,                 -- JSON
    status VARCHAR(20) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    enforced_at DATETIME
);
```

### Users Table

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(120),
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME
);
```

### MetricsHistory Table

```sql
CREATE TABLE metrics_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    device_id VARCHAR(50),
    intent_id VARCHAR(36),
    metadata TEXT                    -- JSON
);
```

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

**Last Updated:** 2026-01-03  
**Total Lines of Code:** 4,704 (source + config + scripts + tests)  
**Core Production Code:** 2,925 lines  
**Security Layer:** 745 lines  
**Configuration:** 825 lines  
**Scripts:** 592 lines  
**Tests:** 362 lines  
**Documentation:** 1,850+ lines  
**Implementation Status:** 100% Core Complete + Security Features Operational  
**Ready for:** Windows Development (Complete) → Raspberry Pi Deployment (Next Phase)  
**Database:** SQLite with 4 tables (intents, policies, users, metrics_history)  
**Authentication:** JWT-based with bcrypt password hashing  
**API Endpoints:** 8 total (5 intent/policy + 3 authentication)
