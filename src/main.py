#!/usr/bin/env python3
"""
Imperium Main Controller - Orchestrates all system components
Coordinates Intent Manager, Policy Engine, Enforcement, and Feedback Loop
"""
import os
import sys
import signal
import logging
import threading
import time
from pathlib import Path
from typing import Optional
import yaml

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from intent_manager.api import app as flask_app, intent_manager
from enforcement.network import NetworkEnforcer
from enforcement.device import DeviceEnforcer
from feedback.monitor import FeedbackEngine
from metrics_exporter import (
    MetricsCollector,
    start_metrics_server,
    record_node_state,
    seed_initial_metrics,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ImperiumController:
    """Main controller for the Imperium IBN system"""
    
    def __init__(self, config_path: str = None):
        """Initialize the controller"""
        self.config = self._load_config(config_path)
        self.running = False
        
        # Components
        self.network_enforcer: Optional[NetworkEnforcer] = None
        self.device_enforcer: Optional[DeviceEnforcer] = None
        self.feedback_engine: Optional[FeedbackEngine] = None
        self.metrics_collector: Optional[MetricsCollector] = None
        
        # Threads
        self.feedback_thread: Optional[threading.Thread] = None
        self.api_thread: Optional[threading.Thread] = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self, config_path: str = None) -> dict:
        """Load configuration from .env or config file"""
        config = {
            # MQTT
            'mqtt_broker_host': os.getenv('MQTT_BROKER_HOST', 'localhost'),
            'mqtt_broker_port': int(os.getenv('MQTT_BROKER_PORT', '1883')),
            
            # Network
            'network_interface': os.getenv('NETWORK_INTERFACE', 'eth0'),
            'enforcement_dry_run': os.getenv('ENFORCEMENT_DRY_RUN', 'false').lower() == 'true',
            
            # API
            'api_host': os.getenv('API_HOST', '0.0.0.0'),
            'api_port': int(os.getenv('API_PORT', '5000')),
            'api_debug': os.getenv('API_DEBUG', 'true').lower() == 'true',
            
            # Feedback
            'feedback_enabled': os.getenv('FEEDBACK_ENABLED', 'true').lower() == 'true',
            'feedback_interval': int(os.getenv('FEEDBACK_CHECK_INTERVAL_SECONDS', '30')),
            
            # Prometheus
            'prometheus_url': os.getenv('PROMETHEUS_URL', 'http://localhost:9090'),
            
            # Paths
            'devices_config': os.getenv('CONFIG_DEVICES_PATH', 'config/devices.yaml'),
        }
        
        # Load devices if config exists
        if os.path.exists(config['devices_config']):
            with open(config['devices_config'], 'r') as f:
                config['devices'] = yaml.safe_load(f)
        
        return config
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.shutdown()
    
    def initialize_components(self):
        """Initialize all system components"""
        logger.info("Initializing Imperium components...")
        
        # 1. Network Enforcer
        logger.info("Initializing Network Enforcer...")
        self.network_enforcer = NetworkEnforcer(
            interface=self.config['network_interface']
        )
        logger.info(f"✓ Network Enforcer ready (interface: {self.config['network_interface']})")
        
        # 2. Device Enforcer (MQTT)
        logger.info("Initializing Device Enforcer...")
        self.device_enforcer = DeviceEnforcer(
            broker_host=self.config['mqtt_broker_host'],
            broker_port=self.config['mqtt_broker_port']
        )
        
        try:
            self.device_enforcer.connect()
            logger.info("✓ Device Enforcer connected to MQTT broker")
        except Exception as e:
            logger.error(f"Failed to connect Device Enforcer: {e}")
            logger.warning("Continuing without MQTT enforcement...")
        
        # 3. Feedback Engine
        if self.config['feedback_enabled']:
            logger.info("Initializing Feedback Engine...")
            self.feedback_engine = FeedbackEngine(
                prometheus_url=self.config['prometheus_url']
            )
            logger.info("✓ Feedback Engine initialized")
        else:
            logger.info("Feedback Engine disabled in configuration")
        
        # 4. Integrate with Intent Manager
        logger.info("Integrating enforcement modules with Intent Manager...")
        intent_manager.network_enforcer = self.network_enforcer
        intent_manager.device_enforcer = self.device_enforcer
        intent_manager.feedback_engine = self.feedback_engine
        logger.info("✓ Components integrated")

        # 5. Prometheus metrics exporter
        logger.info("Starting Prometheus metrics exporter...")
        try:
            metrics_port = int(os.getenv('METRICS_PORT', '8000'))
            start_metrics_server(port=metrics_port)
            self.metrics_collector = MetricsCollector(
                network_enforcer=self.network_enforcer,
                intent_manager=intent_manager,
                poll_interval=5.0,
            )
            self.metrics_collector.start()
            logger.info(f"✓ Prometheus metrics on :{metrics_port}/metrics")

            # Seed ALL per-device gauges and counter labels so every
            # Grafana panel shows data (real defaults) even before the first
            # intent is submitted.
            devices_cfg = self.config.get('devices', {}).get('devices', {})
            seed_initial_metrics(devices_cfg)
            for dev_id, dev_cfg in devices_cfg.items():
                if isinstance(dev_cfg, dict) and 'network' in dev_cfg:
                    record_node_state(dev_id, enabled=True)
            logger.info(f"✓ Seeded metrics for registered devices")
        except Exception as e:
            logger.error(f"Failed to start metrics exporter: {e}")

        logger.info("=" * 60)
        logger.info("All components initialized successfully!")
        logger.info("=" * 60)
    
    def start_feedback_loop(self):
        """Start the feedback monitoring loop"""
        if not self.feedback_engine or not self.config['feedback_enabled']:
            return
        
        def feedback_loop():
            logger.info("Feedback loop started")
            interval = self.config['feedback_interval']
            
            while self.running:
                try:
                    # Check all registered intents
                    for intent_id in list(self.feedback_engine.intent_goals.keys()):
                        satisfaction = self.feedback_engine.check_intent_satisfaction(intent_id)
                        
                        if not satisfaction['satisfied']:
                            logger.warning(f"Intent {intent_id} not satisfied!")
                            logger.warning(f"Violations: {satisfaction['violations']}")
                            
                            # Get recommendations
                            recommendations = self.feedback_engine.recommend_adjustments(intent_id)
                            
                            if recommendations:
                                logger.info(f"Applying {len(recommendations)} adjustments...")
                                # TODO: Auto-apply adjustments if enabled
                                for rec in recommendations:
                                    logger.info(f"  - {rec['action']}: {rec['reason']}")
                    
                    # Sleep until next check
                    time.sleep(interval)
                    
                except Exception as e:
                    logger.error(f"Error in feedback loop: {e}", exc_info=True)
                    time.sleep(interval)
        
        self.feedback_thread = threading.Thread(target=feedback_loop, daemon=True)
        self.feedback_thread.start()
        logger.info(f"✓ Feedback loop started (interval: {self.config['feedback_interval']}s)")
    
    def start_api_server(self):
        """Start the Flask API server in a separate thread"""
        def run_api():
            flask_app.run(
                host=self.config['api_host'],
                port=self.config['api_port'],
                debug=self.config['api_debug'],
                use_reloader=False  # Disable reloader in thread
            )
        
        self.api_thread = threading.Thread(target=run_api, daemon=False)
        self.api_thread.start()
        logger.info(f"✓ Intent Manager API started on {self.config['api_host']}:{self.config['api_port']}")
    
    def start(self):
        """Start the Imperium system"""
        logger.info("=" * 60)
        logger.info("IMPERIUM - Intent-Based Networking Controller")
        logger.info("=" * 60)
        logger.info("")
        
        self.running = True
        
        # Initialize all components
        self.initialize_components()
        
        # Start feedback loop
        if self.config['feedback_enabled']:
            self.start_feedback_loop()
        
        # Display system info
        self._display_system_info()
        
        # Start API server (this will block)
        logger.info("Starting Intent Manager API...")
        logger.info("=" * 60)
        self.start_api_server()
        
        # Wait for API thread
        try:
            self.api_thread.join()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            self.shutdown()
    
    def _display_system_info(self):
        """Display system information"""
        logger.info("")
        logger.info("=" * 60)
        logger.info("System Information:")
        logger.info("=" * 60)
        logger.info(f"API Endpoint:        http://{self.config['api_host']}:{self.config['api_port']}")
        logger.info(f"Health Check:        http://{self.config['api_host']}:{self.config['api_port']}/health")
        logger.info(f"MQTT Broker:         {self.config['mqtt_broker_host']}:{self.config['mqtt_broker_port']}")
        logger.info(f"Prometheus:          {self.config['prometheus_url']}")
        logger.info(f"Network Interface:   {self.config['network_interface']}")
        logger.info(f"Feedback Loop:       {'Enabled' if self.config['feedback_enabled'] else 'Disabled'}")
        
        if self.config.get('devices'):
            device_count = len(self.config['devices'].get('devices', {}))
            logger.info(f"Registered Devices:  {device_count}")
        
        logger.info("=" * 60)
        logger.info("")
        logger.info("Available API Endpoints:")
        logger.info("  POST   /api/v1/intents      - Submit new intent")
        logger.info("  GET    /api/v1/intents      - List all intents")
        logger.info("  GET    /api/v1/intents/<id> - Get specific intent")
        logger.info("  GET    /api/v1/policies     - List all policies")
        logger.info("  GET    /health              - Health check")
        logger.info("=" * 60)
        logger.info("")
        logger.info("System is ready! Press Ctrl+C to shutdown.")
        logger.info("")
    
    def shutdown(self):
        """Shutdown the system gracefully"""
        if not self.running:
            return
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("Shutting down Imperium Controller...")
        logger.info("=" * 60)
        
        self.running = False
        
        # Stop feedback loop
        if self.feedback_thread and self.feedback_thread.is_alive():
            logger.info("Stopping feedback loop...")
            self.feedback_thread.join(timeout=5)
        
        # Disconnect device enforcer
        if self.device_enforcer:
            logger.info("Disconnecting from MQTT broker...")
            try:
                self.device_enforcer.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting MQTT: {e}")
        
        # Clear network policies (optional)
        if self.network_enforcer:
            logger.info("Cleaning up network policies...")
            try:
                # Optionally clear all policies on shutdown
                # self.network_enforcer.clear_policies()
                pass
            except Exception as e:
                logger.error(f"Error clearing policies: {e}")
        
        logger.info("=" * 60)
        logger.info("Shutdown complete. Goodbye!")
        logger.info("=" * 60)
        
        # Exit
        sys.exit(0)


def main():
    """Main entry point"""
    # Check for config file argument
    config_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Create and start controller
    controller = ImperiumController(config_path=config_path)
    
    try:
        controller.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        controller.shutdown()
        sys.exit(1)


if __name__ == '__main__':
    main()
