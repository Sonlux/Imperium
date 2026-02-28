#!/usr/bin/env python3
"""
CO2 Sensor Metrics Collector
Subscribes to MQTT topics from MH-Z19 CO2 sensor and exposes Prometheus metrics
"""
import paho.mqtt.client as mqtt
import json
import logging
import os
import threading
import time
from datetime import datetime
from prometheus_client import start_http_server, Counter, Gauge, Info, Histogram

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
METRICS_PORT = int(os.getenv('METRICS_PORT', 8020))
DEVICE_ID = os.getenv('DEVICE_ID', 'mhz19-01')

# ============== Prometheus Metrics ==============

# CO2 sensor metrics
co2_ppm = Gauge(
    'co2_ppm',
    'CO2 concentration in parts per million',
    ['device_id', 'location']
)

co2_temperature_celsius = Gauge(
    'co2_temperature_celsius',
    'Temperature reading from MH-Z19 sensor',
    ['device_id']
)

co2_readings_total = Counter(
    'co2_readings_total',
    'Total CO2 readings received',
    ['device_id']
)

co2_reading_errors_total = Counter(
    'co2_reading_errors_total',
    'Total CO2 reading errors',
    ['device_id']
)

# Air quality classification
co2_air_quality_level = Gauge(
    'co2_air_quality_level',
    'Air quality level (1=excellent, 2=good, 3=moderate, 4=poor, 5=unhealthy)',
    ['device_id', 'quality']
)

# Device status metrics
co2_sensor_online = Gauge(
    'co2_sensor_online',
    'Whether CO2 sensor is online (1) or offline (0)',
    ['device_id']
)

co2_sensor_uptime_seconds = Gauge(
    'co2_sensor_uptime_seconds',
    'Sensor uptime in seconds',
    ['device_id']
)

# Configuration metrics (set via intents)
co2_sampling_rate_seconds = Gauge(
    'co2_sampling_rate_seconds',
    'Current sampling rate in seconds',
    ['device_id']
)

co2_mqtt_qos_level = Gauge(
    'co2_mqtt_qos_level',
    'Current MQTT QoS level',
    ['device_id']
)

# Histogram for CO2 distribution
co2_ppm_histogram = Histogram(
    'co2_ppm_distribution',
    'Distribution of CO2 readings',
    ['device_id'],
    buckets=[400, 600, 800, 1000, 1200, 1500, 2000, 3000, 5000]
)

# Device info
co2_sensor_info = Info(
    'co2_sensor',
    'CO2 sensor information'
)


def classify_air_quality(ppm: int) -> tuple:
    """Classify air quality based on CO2 PPM"""
    if ppm < 600:
        return 1, 'excellent'
    elif ppm < 800:
        return 2, 'good'
    elif ppm < 1000:
        return 3, 'moderate'
    elif ppm < 1500:
        return 4, 'poor'
    else:
        return 5, 'unhealthy'


class CO2MetricsCollector:
    """Collects CO2 metrics from MQTT and exposes to Prometheus"""
    
    def __init__(self):
        self.device_id = DEVICE_ID
        self.location = os.getenv('LOCATION', 'room-1')
        self.last_reading_time = None
        self.sampling_rate = 5  # Default sampling rate
        self.qos_level = 1  # Default QoS
        
        # Initialize MQTT client
        self.client = mqtt.Client(client_id=f"co2-collector-{self.device_id}")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        # Set initial sensor info
        co2_sensor_info.info({
            'device_id': self.device_id,
            'sensor_type': 'MH-Z19',
            'location': self.location,
            'firmware': 'v1.0.0'
        })
        
        # Initialize gauges
        co2_sampling_rate_seconds.labels(device_id=self.device_id).set(self.sampling_rate)
        co2_mqtt_qos_level.labels(device_id=self.device_id).set(self.qos_level)
        co2_sensor_online.labels(device_id=self.device_id).set(0)
    
    def on_connect(self, client, userdata, flags, rc):
        """Called when connected to MQTT broker"""
        if rc == 0:
            logger.info(f"Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
            
            # Subscribe to device topics
            topics = [
                (f"imperium/devices/{self.device_id}/telemetry", 1),
                (f"imperium/devices/{self.device_id}/status", 1),
                (f"imperium/devices/{self.device_id}/config", 1),
            ]
            for topic, qos in topics:
                client.subscribe(topic, qos)
                logger.info(f"Subscribed to {topic}")
        else:
            logger.error(f"Failed to connect to MQTT broker: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """Called when disconnected from MQTT broker"""
        logger.warning(f"Disconnected from MQTT broker (rc={rc})")
        co2_sensor_online.labels(device_id=self.device_id).set(0)
    
    def on_message(self, client, userdata, msg):
        """Process incoming MQTT messages"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode('utf-8'))
            
            logger.debug(f"Received on {topic}: {payload}")
            
            if topic.endswith('/telemetry'):
                self.process_telemetry(payload)
            elif topic.endswith('/status'):
                self.process_status(payload)
            elif topic.endswith('/config'):
                self.process_config(payload)
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message: {e}")
            co2_reading_errors_total.labels(device_id=self.device_id).inc()
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            co2_reading_errors_total.labels(device_id=self.device_id).inc()
    
    def process_telemetry(self, data: dict):
        """Process telemetry data from CO2 sensor"""
        # Extract CO2 reading
        ppm = data.get('co2_ppm', data.get('co2', 0))
        temp = data.get('temperature', data.get('temp', 0))
        
        if ppm > 0:
            # Update metrics
            co2_ppm.labels(device_id=self.device_id, location=self.location).set(ppm)
            co2_ppm_histogram.labels(device_id=self.device_id).observe(ppm)
            co2_readings_total.labels(device_id=self.device_id).inc()
            
            # Classify air quality
            level, quality = classify_air_quality(ppm)
            co2_air_quality_level.labels(device_id=self.device_id, quality=quality).set(level)
            
            logger.info(f"CO2: {ppm} ppm (air quality: {quality})")
            
            # Update sensor online status
            co2_sensor_online.labels(device_id=self.device_id).set(1)
            self.last_reading_time = time.time()
        
        if temp > 0:
            co2_temperature_celsius.labels(device_id=self.device_id).set(temp)
    
    def process_status(self, data: dict):
        """Process status updates from sensor"""
        status = data.get('status', 'unknown')
        uptime = data.get('uptime', 0)
        
        if status == 'online':
            co2_sensor_online.labels(device_id=self.device_id).set(1)
        else:
            co2_sensor_online.labels(device_id=self.device_id).set(0)
        
        if uptime > 0:
            co2_sensor_uptime_seconds.labels(device_id=self.device_id).set(uptime)
        
        logger.info(f"Sensor status: {status}, uptime: {uptime}s")
    
    def process_config(self, data: dict):
        """Process configuration updates (from intents)"""
        if 'sampling_rate' in data:
            self.sampling_rate = data['sampling_rate']
            co2_sampling_rate_seconds.labels(device_id=self.device_id).set(self.sampling_rate)
            logger.info(f"Updated sampling rate to {self.sampling_rate}s")
        
        if 'qos' in data:
            self.qos_level = data['qos']
            co2_mqtt_qos_level.labels(device_id=self.device_id).set(self.qos_level)
            logger.info(f"Updated QoS level to {self.qos_level}")
        
        if 'priority' in data:
            logger.info(f"Updated priority to {data['priority']}")
    
    def check_sensor_timeout(self):
        """Check if sensor has timed out (no readings)"""
        if self.last_reading_time:
            elapsed = time.time() - self.last_reading_time
            # Consider offline if no reading for 3x sampling rate
            if elapsed > self.sampling_rate * 3:
                co2_sensor_online.labels(device_id=self.device_id).set(0)
    
    def start(self):
        """Start the metrics collector"""
        # Start Prometheus metrics server
        logger.info(f"Starting Prometheus metrics server on port {METRICS_PORT}")
        start_http_server(METRICS_PORT, addr="0.0.0.0")
        
        # Connect to MQTT
        logger.info(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        self.client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        
        # Start MQTT loop in background
        self.client.loop_start()
        
        # Main loop for health checks
        try:
            while True:
                self.check_sensor_timeout()
                time.sleep(10)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            self.client.loop_stop()
            self.client.disconnect()


def simulate_co2_data():
    """Simulate CO2 data for testing when no physical sensor"""
    import random
    
    client = mqtt.Client(client_id="co2-simulator")
    client.connect(MQTT_BROKER, MQTT_PORT)
    
    logger.info("Starting CO2 data simulation...")
    
    base_co2 = 600
    while True:
        # Simulate CO2 fluctuation
        co2 = base_co2 + random.randint(-50, 100)
        temp = 22 + random.uniform(-2, 3)
        
        # Gradually increase CO2 (simulating room occupancy)
        base_co2 = min(1500, base_co2 + random.randint(-10, 20))
        
        telemetry = {
            'co2_ppm': co2,
            'temperature': round(temp, 1),
            'timestamp': datetime.now().isoformat()
        }
        
        client.publish(
            f"imperium/devices/{DEVICE_ID}/telemetry",
            json.dumps(telemetry),
            qos=1
        )
        
        logger.info(f"Simulated CO2: {co2} ppm, temp: {temp:.1f}°C")
        
        # Reset if CO2 gets too high (window opened)
        if base_co2 > 1400:
            base_co2 = 500
        
        time.sleep(5)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--simulate':
        # Run simulator in background thread
        sim_thread = threading.Thread(target=simulate_co2_data, daemon=True)
        sim_thread.start()
    
    collector = CO2MetricsCollector()
    collector.start()
