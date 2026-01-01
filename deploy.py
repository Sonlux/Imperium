#!/usr/bin/env python3
"""
Complete project setup and deployment script
Creates all directories and core implementation files
"""
import os
import pathlib

# Base path
BASE = pathlib.Path(__file__).parent

# Directory structure
DIRS = [
    'src/intent_manager',
    'src/policy_engine', 
    'src/enforcement',
    'src/feedback',
    'src/iot_simulator',
    'config',
    'monitoring/prometheus',
    'monitoring/grafana/provisioning/datasources',
    'monitoring/grafana/provisioning/dashboards',
    'scripts',
    'tests'
]

# File contents
FILES = {
    'src/__init__.py': '"""Imperium Package"""',
    'src/intent_manager/__init__.py': '"""Intent Manager Package"""',
    'src/policy_engine/__init__.py': '"""Policy Engine Package"""',
    'src/enforcement/__init__.py': '"""Enforcement Package"""',
    'src/feedback/__init__.py': '"""Feedback Loop Package"""',
    'src/iot_simulator/__init__.py': '"""IoT Simulator Package"""',
    
    'config/mosquitto.conf': '''# Mosquitto MQTT Broker Configuration

# Allow anonymous connections for development
allow_anonymous true

# MQTT Protocol
listener 1883
protocol mqtt

# WebSocket Support
listener 9001
protocol websockets

# Persistence
persistence true
persistence_location /mosquitto/data/

# Logging
log_dest file /mosquitto/log/mosquitto.log
log_dest stdout
log_type all
''',
    
    'monitoring/prometheus/prometheus.yml': '''global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'intent-manager'
    static_configs:
      - targets: ['host.docker.internal:5000']

  - job_name: 'iot-nodes'
    static_configs:
      - targets: ['iot-node-1:8000']
''',

    'monitoring/grafana/provisioning/datasources/prometheus.yml': '''apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
''',
}

def create_structure():
    """Create all directories"""
    for dir_path in DIRS:
        full_path = BASE / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created: {dir_path}")

def create_files():
    """Create all configuration files"""
    for file_path, content in FILES.items():
        full_path = BASE / file_path
        full_path.write_text(content, encoding='utf-8')
        print(f"✓ Created: {file_path}")

def main():
    print("=" * 60)
    print("Imperium Project Setup")
    print("=" * 60)
    print()
    
    print("Creating directory structure...")
    create_structure()
    print()
    
    print("Creating configuration files...")
    create_files()
    print()
    
    print("=" * 60)
    print("✅ Project structure created successfully!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Start Docker services: docker-compose up -d")
    print("3. Run Intent Manager: python src/intent_manager/api.py")
    print()
    print("See SETUP.md for detailed instructions")

if __name__ == '__main__':
    main()
