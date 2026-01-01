#!/usr/bin/env python3
"""
IoT Node Simulator - Simulates IoT device behavior
Publishes sensor data via MQTT and responds to control messages
"""
import paho.mqtt.client as mqtt
import json
import time
import random
import logging
import os
from datetime import datetime
from prometheus_client import start_http_server, Counter, Gauge

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
messages_sent = Counter('iot_messages_sent_total', 'Total messages sent')
messages_received = Counter('iot_messages_received_total', 'Total messages received')
sensor_value = Gauge('iot_sensor_value', 'Current sensor reading')
bandwidth_usage = Gauge('iot_bandwidth_bytes', 'Bandwidth usage in bytes')


class IoTNode:
    """Simulates an IoT device"""
    
    def __init__(self, node_id, broker_host='mosquitto', broker_port=1883):
        self.node_id = node_id
        self.broker_host = broker_host
        self.broker_port = broker_port
        
        # Node configuration
        self.config = {
            'sampling_rate': 5,  # seconds
            'qos': 0,
            'priority': 'normal',
            'bandwidth_limit': None,
            'enabled': True
        }
        
        # MQTT client
        self.client = mqtt.Client(client_id=node_id)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        # Topics
        self.data_topic = f"iot/{node_id}/data"
        self.control_topic = f"iot/{node_id}/control"
        self.status_topic = f"iot/{node_id}/status"
        
        self.running = False
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            logger.info(f"Node {self.node_id} connected to MQTT broker")
            # Subscribe to control messages
            client.subscribe(self.control_topic, qos=1)
            # Publish status
            self.publish_status()
        else:
            logger.error(f"Connection failed with code {rc}")
    
    def on_message(self, client, userdata, msg):
        """Handle incoming control messages"""
        try:
            payload = json.loads(msg.payload.decode())
            logger.info(f"Received control message: {payload}")
            messages_received.inc()
            
            # Update configuration
            if 'sampling_rate' in payload:
                self.config['sampling_rate'] = payload['sampling_rate']
                logger.info(f"Updated sampling rate to {payload['sampling_rate']}s")
            
            if 'qos' in payload:
                self.config['qos'] = payload['qos']
                logger.info(f"Updated QoS to {payload['qos']}")
            
            if 'priority' in payload:
                self.config['priority'] = payload['priority']
                logger.info(f"Updated priority to {payload['priority']}")
            
            if 'enabled' in payload:
                self.config['enabled'] = payload['enabled']
                logger.info(f"Node enabled: {payload['enabled']}")
            
            # Acknowledge configuration change
            self.publish_status()
            
        except Exception as e:
            logger.error(f"Error processing control message: {e}")
    
    def publish_status(self):
        """Publish current node status"""
        status = {
            'node_id': self.node_id,
            'timestamp': datetime.now().isoformat(),
            'config': self.config,
            'status': 'online' if self.running else 'offline'
        }
        
        self.client.publish(
            self.status_topic,
            json.dumps(status),
            qos=1,
            retain=True
        )
    
    def generate_sensor_data(self):
        """Generate simulated sensor data"""
        return {
            'node_id': self.node_id,
            'timestamp': datetime.now().isoformat(),
            'temperature': round(20 + random.uniform(-5, 5), 2),
            'humidity': round(50 + random.uniform(-10, 10), 2),
            'pressure': round(1013 + random.uniform(-20, 20), 2),
            'battery': round(random.uniform(80, 100), 1)
        }
    
    def publish_data(self):
        """Publish sensor data"""
        if not self.config['enabled']:
            return
        
        data = self.generate_sensor_data()
        payload = json.dumps(data)
        
        result = self.client.publish(
            self.data_topic,
            payload,
            qos=self.config['qos']
        )
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            messages_sent.inc()
            bandwidth_usage.set(len(payload.encode()))
            sensor_value.set(data['temperature'])
            logger.info(f"Published: {data['temperature']}°C")
        else:
            logger.error(f"Failed to publish data: {result.rc}")
    
    def run(self):
        """Main run loop"""
        logger.info(f"Starting IoT Node: {self.node_id}")
        logger.info(f"Connecting to {self.broker_host}:{self.broker_port}")
        
        # Start Prometheus metrics server
        metrics_port = 8000 + int(self.node_id.split('-')[-1])
        start_http_server(metrics_port)
        logger.info(f"Metrics available at http://localhost:{metrics_port}")
        
        # Connect to MQTT broker
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            self.running = True
            
            # Main data publishing loop
            while self.running:
                self.publish_data()
                time.sleep(self.config['sampling_rate'])
                
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            self.running = False
            self.client.loop_stop()
            self.client.disconnect()
        except Exception as e:
            logger.error(f"Error: {e}")
            self.running = False


if __name__ == '__main__':
    # Get configuration from environment
    node_id = os.getenv('NODE_ID', 'node-1')
    broker = os.getenv('MQTT_BROKER', 'localhost')
    port = int(os.getenv('MQTT_PORT', '1883'))
    
    # Create and run node
    node = IoTNode(node_id, broker, port)
    node.run()
