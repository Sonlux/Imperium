# Imperium Codebase Index

## Project Structure

```
Imperium/
├── README.md                    # Project overview
├── QUICKSTART.md                # Quick start guide
├── SETUP.md                     # Full setup instructions
├── RASPBERRY_PI_SETUP.md        # Raspberry Pi deployment guide
├── CODEBASE_INDEX.md            # This file
├── task.md                      # Development task tracker
├── LICENSE                      # Project license
├── Makefile                     # Build/run shortcuts
├── requirements.txt             # Python dependencies
├── docker-compose.yml           # Service stack (MQTT, Prometheus, Grafana)
├── Dockerfile.iot-node          # IoT node simulator container
├── .env.example                 # Environment variable template
├── .gitignore                   # Git ignore rules
│
├── src/                         # Core application source code
│   ├── main.py                  # Flask app entry point (port 5000)
│   ├── auth.py                  # JWT authentication
│   ├── rate_limiter.py          # API rate limiting
│   ├── database.py              # SQLite persistence
│   ├── intent_manager/
│   │   ├── api.py               # REST API endpoints
│   │   ├── parser.py            # NLP intent parser (7 intent types)
│   │   └── auth_endpoints.py    # Auth-related endpoints
│   ├── policy_engine/
│   │   └── engine.py            # Intent → policy translation
│   ├── enforcement/
│   │   ├── network.py           # Linux tc/netem enforcement
│   │   └── device.py            # MQTT device command publisher
│   ├── feedback/
│   │   └── monitor.py           # Prometheus metric monitoring
│   └── iot_simulator/
│       ├── node.py              # Docker IoT node simulator
│       └── co2_collector.py     # CO2 metric bridge (ESP32→Prometheus)
│
├── config/                      # Configuration files
│   ├── devices.yaml             # Device registry
│   ├── intent_grammar.yaml      # NLP intent patterns
│   ├── policy_templates.yaml    # TC policy templates
│   ├── mosquitto.conf           # MQTT broker config
│   ├── imperium.service         # systemd service unit
│   ├── imperium.cron            # Cron jobs (backups)
│   └── logrotate.conf           # Log rotation config
│
├── esp32-cam-node/              # ESP32-CAM firmware (ESP-IDF)
│   ├── main/
│   │   └── esp32_cam_main.c     # Camera node: capture, MQTT, metrics
│   ├── components/esp-camera/   # ESP32 camera driver library
│   ├── CMakeLists.txt           # Build config
│   ├── partitions.csv           # Flash partition layout (3MB app)
│   └── sdkconfig.defaults       # Default build settings
│
├── esp32-audio-node/            # ESP32 Audio Node firmware (ESP-IDF)
│   ├── main/
│   │   ├── main.cpp             # Audio node entry point
│   │   ├── i2s_audio.cpp/h      # INMP441 I2S microphone driver
│   │   ├── mqtt_handler.cpp/h   # MQTT pub/sub handler
│   │   ├── policy_handler.cpp/h # IBN policy application
│   │   └── config.h             # WiFi/MQTT/device config
│   ├── CMakeLists.txt
│   └── sdkconfig.defaults
│
├── esp32-mhz19-node/            # ESP32 MH-Z19 CO2 Sensor firmware
│   ├── main/
│   │   ├── main.c               # CO2 node entry point
│   │   ├── mhz19.c/h            # MH-Z19B UART driver
│   │   ├── mqtt_handler.c/h     # MQTT pub/sub
│   │   ├── wifi_handler.c/h     # WiFi connection
│   │   └── config.h             # WiFi/MQTT/device config
│   ├── CMakeLists.txt
│   └── sdkconfig.defaults
│
├── monitoring/                  # Observability stack config
│   ├── prometheus/
│   │   └── prometheus.yml       # Scrape targets config
│   └── grafana/
│       └── provisioning/
│           └── dashboards/
│               ├── dashboard.yml               # Dashboard provisioner config
│               ├── imperium-overview.json       # System overview dashboard
│               ├── imperium-devices.json        # Device management dashboard
│               ├── esp32-mhz19-1-dashboard.json # CO2 sensor dashboard
│               ├── esp32-audio-1-dashboard.json  # Audio sensor dashboard
│               └── iot-nodes-dashboard.json      # 10 simulated nodes dashboard
│
├── scripts/                     # Utility scripts
│   ├── init_database.py         # Database initialization
│   ├── generate_secrets.py      # JWT secret generation
│   ├── demo_menu.py             # Interactive demo menu
│   ├── backup.sh                # Config/DB backup script
│   ├── recovery_test.sh         # Disaster recovery test
│   ├── check_status.sh          # Service health check
│   ├── test_api.py              # API endpoint tests
│   ├── test_esp32_intent.py     # ESP32 intent tests
│   ├── test_esp32_intents.py    # Multi-intent ESP32 tests
│   ├── test_esp32_advanced_intents.py  # Advanced ESP32 tests
│   └── aliases.sh               # Shell aliases for convenience
│
├── tests/                       # Automated test suite
│   ├── test_core.py             # Unit tests (parser, engine)
│   └── test_integration.py      # Integration tests
│
├── docs/                        # Documentation
│   ├── demo.md                  # Demo walkthrough
│   ├── DEMO_COMMANDS.md         # Demo command reference
│   ├── DEMO_QUICK_REFERENCE.md  # Quick reference card
│   ├── DEMO_VERIFICATION_REPORT.md  # Test verification report
│   ├── DEPLOYMENT_SUMMARY.md    # Deployment summary
│   ├── ESP32_ADVANCED_CONTROLS.md   # ESP32 advanced controls
│   ├── ESP32_DEMO_INTEGRATION.md    # ESP32 demo integration
│   ├── ESP32_INTEGRATION_FINAL.md   # ESP32 integration report
│   ├── DISASTER_RECOVERY.md     # Disaster recovery procedures
│   ├── MONITORING_GUIDE.md      # Monitoring setup guide
│   ├── PROMETHEUS_QUERIES.md    # Useful PromQL queries
│   ├── PROGRESS.md              # Development progress log
│   ├── PRD_CLI_IMPLEMENTATION.md    # CLI implementation details
│   ├── SECURITY.md              # Security overview
│   ├── SECURITY_IMPLEMENTATION.md   # Security implementation
│   ├── SECURITY_CHECKLIST.md    # Security checklist
│   └── SECURITY_COMPLETE.md     # Security completion report
│
├── data/                        # Runtime data (gitignored)
│   └── imperium.db              # SQLite database
├── logs/                        # Runtime logs (gitignored)
└── backups/                     # Config backups (gitignored)
```

## Key Services

| Service | Port | Description |
|---------|------|-------------|
| Imperium API | 5000 | Flask REST API |
| MQTT Broker | 1883 | Mosquitto message broker |
| Prometheus | 9090 | Metrics collection |
| Grafana | 3000 | Dashboard visualization |
| IoT Nodes | 8001-8010 | Simulated node metrics |

## Hardware Nodes

| Device ID | Hardware | Metrics |
|-----------|----------|---------|
| esp32-mhz19-1 | MH-Z19B CO2 Sensor | co2_ppm, temperature_celsius |
| esp32-audio-1 | INMP441 Microphone | audio_rms_level_db, audio_gain |
| esp32-cam-1 | OV2640 Camera | frames_captured, frame_size_bytes |

## Intent Types

1. **Prioritize** - Set device/group priority
2. **Limit bandwidth** - Bandwidth caps (tc htb)
3. **Reduce latency** - Latency targets (tc netem)
4. **Set QoS** - MQTT QoS levels
5. **Set sampling rate** - Sensor frequency
6. **Set audio gain** - Audio amplification
7. **Set camera resolution** - Camera quality
