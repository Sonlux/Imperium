# Raspberry Pi Setup Guide for Imperium

**Platform:** Raspberry Pi 4 (Debian 13 "Trixie")  
**Date:** 2026-01-21  
**Status:** ✅ Docker Optional - Can run standalone or with Docker

---

## 🎯 Two Deployment Options

### **Option A: Standalone (No Docker Required)**
Run Imperium controller directly with Python - uses system MQTT/Prometheus

### **Option B: Docker-Based (Recommended for Full Stack)**
Run MQTT, Prometheus, Grafana, and IoT simulators in containers

---

## ✅ What's Already Installed

```bash
✅ Raspberry Pi OS (Debian 13 "Trixie")
✅ Python 3.13.5
✅ Docker 29.1.3 + Docker Compose 5.0.1
✅ Virtual environment (venv) created
✅ Traffic control tools: tc (iproute2-6.15.0), iptables
✅ Docker services running:
   - MQTT Broker (Mosquitto) - Port 1883
   - Prometheus - Port 9090
   - Grafana - Port 3000
   - IoT Simulator Node
```

---

## 📋 What Still Needs Installation

### 1. **Complete Python Dependencies**

Your venv has core packages but missing some optional ones:

```bash
cd /home/imperium/Imperium
source venv/bin/activate

# Install all dependencies from requirements.txt
pip install -r requirements.txt

# Or install only essential packages (faster):
pip install pyyaml prometheus-client sqlalchemy requests netifaces
```

**Current Status:**
```
✅ Installed: Flask, flask-cors, paho-mqtt, bcrypt, sqlalchemy, pyjwt
❌ Missing: PyYAML, prometheus-client, pandas, numpy, scapy, netifaces, pytest
```

---

## 🚀 Quick Start Guide

### **Step 1: Complete Python Setup**

```bash
# Activate virtual environment
cd /home/imperium/Imperium
source venv/bin/activate

# Install missing essential packages
pip install pyyaml==6.0.1 prometheus-client==0.19.0 netifaces==0.11.0

# Optional (for testing and data processing):
pip install pytest==7.4.3 pytest-cov==4.1.0 pandas==2.1.4 numpy==1.26.2
```

### **Step 2: Verify Environment Configuration**

```bash
# Check if .env file exists and is configured
cat .env | head -20

# If not, copy from template
cp .env.example .env

# Edit key settings:
nano .env
# Set: NETWORK_INTERFACE=eth0
# Set: JWT_ENABLED=true
# Set: MOCK_NETWORK_ENFORCEMENT=false
```

### **Step 3: Initialize Database**

```bash
# Create required directories
mkdir -p data logs

# Initialize database with admin user
python scripts/init_database.py

# You should see:
# ✓ Database created successfully
# ✓ Admin user created (username: admin, password: admin)
```

### **Step 4: Start the System**

#### **Option A: Manual Start (Development)**

```bash
# Start Docker services (already running)
docker compose up -d

# Start Imperium controller
PYTHONPATH=/home/imperium/Imperium python src/main.py

# API will be available at: http://localhost:5000
```

#### **Option B: Systemd Service (Production)**

```bash
# Service already installed, just start it
sudo systemctl start imperium

# Check status
sudo systemctl status imperium

# View logs
journalctl -u imperium -f

# Enable auto-start on boot
sudo systemctl enable imperium
```

### **Step 5: Test the System**

```bash
# Health check
curl http://localhost:5000/health

# Login to get JWT token
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'

# Submit an intent (replace TOKEN with JWT from login)
curl -X POST http://localhost:5000/api/v1/intents \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description": "Prioritize temperature sensors"}'
```

---

## 🐳 Docker Services Explained

### **Do You Need Docker?**

**Short Answer: No, but it's helpful!**

- **Imperium Core (Python):** Runs standalone, NO Docker needed
- **Optional Services:** MQTT, Prometheus, Grafana - can use Docker OR install system-wide

### **What Docker Provides:**

1. **MQTT Broker (Mosquitto)** - Port 1883
   - Used for IoT device communication
   - Alternative: Install `sudo apt install mosquitto mosquitto-clients`

2. **Prometheus** - Port 9090
   - Metrics collection and storage
   - Alternative: Install `sudo apt install prometheus`

3. **Grafana** - Port 3000
   - Visualization dashboards
   - Alternative: Install from Grafana repos

4. **IoT Simulators** - For testing
   - Simulates IoT devices for development
   - Not needed if using real ESP32/IoT devices

### **Current Docker Status:**

```bash
# Check running services
docker compose ps

# Stop Docker services (if you want standalone)
docker compose down

# Start Docker services
docker compose up -d

# View logs
docker compose logs -f
```

---

## 🔧 System Requirements Check

Run this command to verify everything:

```bash
# Create verification script
cat > /tmp/verify_imperium.sh << 'EOF'
#!/bin/bash
echo "=== Imperium System Verification ==="
echo ""
echo "✓ OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "✓ Kernel: $(uname -r)"
echo "✓ Python: $(python3 --version)"
echo ""
echo "--- Docker ---"
docker --version 2>/dev/null && echo "✓ Docker installed" || echo "✗ Docker not found"
docker compose version 2>/dev/null && echo "✓ Docker Compose installed" || echo "✗ Docker Compose not found"
echo ""
echo "--- Network Tools ---"
tc -Version 2>/dev/null && echo "✓ tc (traffic control)" || echo "✗ tc not found"
which iptables >/dev/null 2>&1 && echo "✓ iptables" || echo "✗ iptables not found"
echo ""
echo "--- Python Packages (venv) ---"
source ~/Imperium/venv/bin/activate 2>/dev/null
pip show flask >/dev/null 2>&1 && echo "✓ Flask" || echo "✗ Flask"
pip show pyyaml >/dev/null 2>&1 && echo "✓ PyYAML" || echo "✗ PyYAML (install needed)"
pip show prometheus-client >/dev/null 2>&1 && echo "✓ Prometheus client" || echo "✗ Prometheus client (install needed)"
pip show sqlalchemy >/dev/null 2>&1 && echo "✓ SQLAlchemy" || echo "✗ SQLAlchemy"
pip show paho-mqtt >/dev/null 2>&1 && echo "✓ paho-mqtt" || echo "✗ paho-mqtt"
echo ""
echo "--- Files ---"
[ -f ~/Imperium/.env ] && echo "✓ .env configured" || echo "✗ .env missing (copy from .env.example)"
[ -f ~/Imperium/data/imperium.db ] && echo "✓ Database initialized" || echo "✗ Database not initialized (run init_database.py)"
[ -d ~/Imperium/venv ] && echo "✓ Virtual environment" || echo "✗ Virtual environment missing"
echo ""
echo "--- Services ---"
curl -s http://localhost:5000/health >/dev/null 2>&1 && echo "✓ Imperium API running" || echo "✗ Imperium API not running"
curl -s http://localhost:1883 >/dev/null 2>&1 && echo "? MQTT broker" || echo "? MQTT broker (expected)"
curl -s http://localhost:9090/-/healthy >/dev/null 2>&1 && echo "✓ Prometheus running" || echo "✗ Prometheus not running"
curl -s http://localhost:3000 >/dev/null 2>&1 && echo "✓ Grafana running" || echo "✗ Grafana not running"
echo ""
echo "=== Verification Complete ==="
EOF

chmod +x /tmp/verify_imperium.sh
bash /tmp/verify_imperium.sh
```

---

## 📝 Installation Commands Summary

### **Essential Setup (5 minutes):**

```bash
# 1. Install missing Python packages
cd /home/imperium/Imperium
source venv/bin/activate
pip install pyyaml prometheus-client netifaces

# 2. Verify environment
ls -la .env || cp .env.example .env

# 3. Initialize database
python scripts/init_database.py

# 4. Start system
PYTHONPATH=/home/imperium/Imperium python src/main.py
```

### **Full Setup with Testing (15 minutes):**

```bash
# 1. Install all dependencies
cd /home/imperium/Imperium
source venv/bin/activate
pip install -r requirements.txt

# 2. Initialize database
mkdir -p data logs
python scripts/init_database.py

# 3. Start Docker services
docker compose up -d

# 4. Start Imperium with systemd
sudo systemctl start imperium
sudo systemctl status imperium

# 5. Test API
curl http://localhost:5000/health

# 6. Open Grafana
# Visit: http://raspberrypi.local:3000 (admin/imperium2026)
```

---

## 🌐 Access URLs

Once running, access these services:

```
Imperium API:     http://raspberrypi.local:5000
API Health:       http://raspberrypi.local:5000/health
Grafana:          http://raspberrypi.local:3000 (admin/imperium2026)
Prometheus:       http://raspberrypi.local:9090
MQTT Broker:      mqtt://raspberrypi.local:1883
```

---

## 🔍 Troubleshooting

### **Issue: "ModuleNotFoundError: No module named 'yaml'"**
```bash
source venv/bin/activate
pip install pyyaml
```

### **Issue: "Cannot connect to MQTT broker"**
```bash
# Check if MQTT is running
docker compose ps | grep mosquitto
# OR
sudo systemctl status mosquitto

# Restart if needed
docker compose restart mosquitto
```

### **Issue: "Permission denied: tc command"**
```bash
# tc commands require sudo
sudo tc qdisc show dev eth0

# Or run Imperium with sudo (not recommended for production)
sudo PYTHONPATH=/home/imperium/Imperium python src/main.py
```

### **Issue: "Database locked"**
```bash
# Stop any running instances
pkill -f "python src/main.py"
sudo systemctl stop imperium

# Check database
sqlite3 data/imperium.db "PRAGMA integrity_check;"
```

---

## 📚 Next Steps

After installation:

1. **Change Default Password**
   ```bash
   # Use API to change admin password
   curl -X POST http://localhost:5000/api/v1/auth/change-password \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{"old_password": "admin", "new_password": "YourSecurePassword123!"}'
   ```

2. **Configure Physical IoT Devices**
   - Edit `config/devices.yaml`
   - Add your ESP32/IoT device IPs and configs
   - Test MQTT connection

3. **Test Network Enforcement**
   ```bash
   # Submit intent to limit bandwidth
   curl -X POST http://localhost:5000/api/v1/intents \
     -H "Authorization: Bearer TOKEN" \
     -d '{"description": "Limit camera bandwidth to 1 Mbps"}'
   
   # Verify tc rules applied
   sudo tc qdisc show dev eth0
   ```

4. **Monitor in Grafana**
   - Open http://raspberrypi.local:3000
   - View "Imperium Overview" dashboard
   - Check device metrics and policy enforcement

---

## 📖 Documentation

- **Main README:** [README.md](README.md)
- **API Documentation:** [API Reference in README](README.md#api-reference)
- **Security Guide:** [docs/SECURITY.md](docs/SECURITY.md)
- **Deployment Summary:** [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)
- **Task Tracking:** [task.md](task.md)

---

## ⚠️ Important Notes

1. **Docker is OPTIONAL** - Imperium core runs standalone
2. **Network enforcement requires sudo** - tc/iptables commands need root
3. **Change default passwords** - admin/admin is development-only
4. **Virtual environment** - Always activate venv before running Python
5. **PYTHONPATH** - Set to project root for imports to work

---

**Setup Status:** ✅ 90% Complete - Just need to install PyYAML and prometheus-client!
