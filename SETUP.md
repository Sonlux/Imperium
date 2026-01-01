# Setup Instructions for Imperium Project

## Prerequisites

### Required Software

1. **Python 3.8+** - [Download](https://www.python.org/downloads/)
2. **Docker Desktop** - [Download](https://www.docker.com/products/docker-desktop/)
3. **Git** - [Download](https://git-scm.com/downloads)

### For Development on Windows

- PowerShell 7+ recommended but not required
- Windows 10/11 with WSL2 (optional, for better Docker experience)

## Quick Start

### 1. Create Project Structure

Run the setup batch script:

```cmd
setup.bat
```

Or manually with Python:

```cmd
python setup_structure.py
```

### 2. Install Python Dependencies

```cmd
pip install -r requirements.txt
```

Or use a virtual environment (recommended):

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Start Infrastructure Services

Start MQTT, Prometheus, and Grafana:

```cmd
docker-compose up -d
```

Verify services are running:

```cmd
docker-compose ps
```

### 4. Start the Intent Manager API

```cmd
python src\intent_manager\api.py
```

The API will be available at `http://localhost:5000`

## Service Endpoints

- **Intent Manager API**: http://localhost:5000
- **Grafana Dashboard**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **MQTT Broker**: localhost:1883

## Testing the System

### Submit an Intent

Using curl:

```cmd
curl -X POST http://localhost:5000/api/v1/intents ^
  -H "Content-Type: application/json" ^
  -d "{\"description\": \"Prioritize device node-1\", \"type\": \"priority\"}"
```

Using Python:

```python
import requests

response = requests.post(
    'http://localhost:5000/api/v1/intents',
    json={
        'description': 'Prioritize device node-1',
        'type': 'priority'
    }
)
print(response.json())
```

### List All Intents

```cmd
curl http://localhost:5000/api/v1/intents
```

## Project Structure

```
imperium/
├── src/
│   ├── intent_manager/    # Intent acquisition & parsing
│   ├── policy_engine/     # Policy generation
│   ├── enforcement/       # Network & device enforcement
│   ├── feedback/          # Monitoring & feedback loop
│   └── iot_simulator/     # IoT node simulation
├── config/                # Configuration files
├── monitoring/            # Prometheus & Grafana configs
├── scripts/               # Utility scripts
├── tests/                 # Test files
├── docker-compose.yml     # Service orchestration
└── requirements.txt       # Python dependencies
```

## Development Workflow

### For Raspberry Pi Deployment

1. **Prepare the Raspberry Pi**:

   ```bash
   # On Raspberry Pi
   sudo apt update
   sudo apt install python3-pip docker.io
   sudo usermod -aG docker $USER
   ```

2. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd imperium
   ```

3. **Install dependencies**:

   ```bash
   pip3 install -r requirements.txt
   ```

4. **Start services**:
   ```bash
   docker-compose up -d
   python3 src/intent_manager/api.py
   ```

### Running Tests

```cmd
pytest tests/
```

With coverage:

```cmd
pytest --cov=src tests/
```

## Troubleshooting

### Docker Issues

- Ensure Docker Desktop is running
- Check firewall settings for ports 1883, 3000, 5000, 9090
- Try `docker-compose down` and `docker-compose up -d` to restart

### Python Import Errors

- Ensure you're in the project root directory
- Activate virtual environment if using one
- Reinstall requirements: `pip install -r requirements.txt --force-reinstall`

### MQTT Connection Issues

- Verify Mosquitto container is running: `docker ps`
- Check logs: `docker logs imperium-mqtt`
- Test connection: `docker exec -it imperium-mqtt mosquitto_sub -t test/#`

## Next Steps

1. ✅ Setup complete - Infrastructure running
2. Implement enforcement module (tc, iptables wrappers)
3. Create IoT node simulator
4. Build feedback loop with Prometheus metrics
5. Integrate all components
6. Test on Raspberry Pi hardware

## Support

For issues or questions, refer to:

- Project README.md
- task.md for implementation checklist
- Docker logs: `docker-compose logs -f`
