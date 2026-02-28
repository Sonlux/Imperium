# Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Setup Environment

Run the setup script:

```cmd
start_setup.bat
```

This creates all directories and configuration files.

### Step 2: Install Dependencies

```cmd
pip install -r requirements.txt
```

Or use a virtual environment (recommended):

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3: Start Services

#### Option A: Full Docker Stack (Recommended)

```cmd
docker-compose up -d
```

This starts:

- MQTT Broker (port 1883)
- Prometheus (port 9090)
- Grafana (port 3000)
- IoT Node Simulator

#### Option B: Development Mode (API Only)

```cmd
python src\intent_manager\api.py
```

## 🧪 Test the System

Run the test script:

```cmd
python scripts\test_api.py
```

Or submit an intent manually:

```cmd
curl -X POST http://localhost:5000/api/v1/intents ^
  -H "Content-Type: application/json" ^
  -d "{\"description\": \"Prioritize device node-1\", \"type\": \"priority\"}"
```

## 📊 View Dashboards

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **API Docs**: http://localhost:5000/health

## 🎯 Example Intents

Try these intents:

1. **Priority**: "Prioritize device node-1"
2. **Bandwidth**: "Limit bandwidth to 100 mbps for node-2"
3. **Latency**: "Reduce latency to 50ms"
4. **QoS**: "Set QoS level 2 for critical devices"

## 📁 Project Structure

```
imperium/
├── src/
│   ├── intent_manager/   # REST API + Parser
│   ├── policy_engine/    # Policy Generation
│   ├── enforcement/      # Network + Device Control
│   ├── feedback/         # Monitoring Loop
│   └── iot_simulator/    # IoT Node Simulation
├── config/               # MQTT, Prometheus configs
├── monitoring/           # Grafana dashboards
└── scripts/              # Utility scripts
```

## 🔧 Troubleshooting

**API won't start?**

- Check Python version: `python --version` (need 3.8+)
- Install dependencies: `pip install -r requirements.txt`

**Docker issues?**

- Ensure Docker Desktop is running
- Try: `docker-compose down && docker-compose up -d`

**Can't connect to services?**

- Check ports: 1883 (MQTT), 3000 (Grafana), 5000 (API), 9090 (Prometheus)
- Check firewall settings

## 📚 Next Steps

1. ✅ **Complete setup** - Run start_setup.bat
2. ✅ **Start services** - docker-compose up -d
3. ✅ **Test API** - python scripts/test_api.py
4. 📝 **Submit intents** - Use API or web interface
5. 📊 **Monitor metrics** - View Grafana dashboards
6. 🔧 **Deploy to Pi** - Follow SETUP.md for Raspberry Pi deployment

## 💡 Tips

- Use virtual environment to avoid dependency conflicts
- Check logs: `docker-compose logs -f`
- Run tests: `pytest tests/`
- View API status: `curl http://localhost:5000/health`

For detailed instructions, see **SETUP.md**
