#!/usr/bin/env python3
"""
Device Enforcement Module - Controls IoT devices via MQTT
Sends configuration and control messages to IoT nodes
"""
import paho.mqtt.client as mqtt
import json
import logging
from typing import Dict, Any
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeviceEnforcer:
    """Enforces policies on IoT devices via MQTT"""
    
    def __init__(self, broker_host='localhost', broker_port=1883):
        self.broker_host = broker_host
        self.broker_port = broker_port
        
        self.client = mqtt.Client(client_id='device-enforcer')
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        self.connected = False
        self.device_status = {}
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            logger.info("Device Enforcer connected to MQTT broker")
            self.connected = True
            # Subscribe to all device status topics
            client.subscribe("iot/+/status", qos=1)
        else:
            logger.error(f"Connection failed with code {rc}")
    
    def on_message(self, client, userdata, msg):
        """Handle incoming device status messages"""
        try:
            payload = json.loads(msg.payload.decode())
            node_id = payload.get('node_id')
            self.device_status[node_id] = payload
            logger.debug(f"Updated status for {node_id}")
        except Exception as e:
            logger.error(f"Error processing status message: {e}")
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            
            # Wait for connection
            timeout = 5
            while not self.connected and timeout > 0:
                time.sleep(0.5)
                timeout -= 0.5
            
            if not self.connected:
                raise Exception("Failed to connect to MQTT broker")
            
            logger.info("Successfully connected to MQTT broker")
            
        except Exception as e:
            logger.error(f"Connection error: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("Disconnected from MQTT broker")
    
    def apply_policy(self, policy: Dict[str, Any]) -> bool:
        """
        Apply a device policy
        
        Args:
            policy: Policy dictionary with type, target, and parameters
            
        Returns:
            bool: Success status
        """
        policy_type = policy.get('policy_type')
        
        if policy_type == 'qos_control':
            return self._apply_qos_policy(policy)
        elif policy_type == 'device_config':
            return self._apply_device_config(policy)
        elif policy_type == 'sample_rate':
            return self._apply_sample_rate_policy(policy)
        elif policy_type == 'sampling_interval':
            return self._apply_sampling_interval_policy(policy)
        elif policy_type == 'device_control':
            return self._apply_device_control_policy(policy)
        elif policy_type == 'publish_interval':
            return self._apply_publish_interval_policy(policy)
        elif policy_type == 'audio_gain':
            return self._apply_audio_gain_policy(policy)
        elif policy_type in ('camera_resolution', 'camera_quality',
                             'camera_brightness', 'camera_framerate',
                             'camera_control'):
            return self._apply_camera_policy(policy)
        else:
            logger.warning(f"Unsupported policy type for devices: {policy_type}")
            return False
    
    def _apply_qos_policy(self, policy: Dict) -> bool:
        """Apply QoS policy to device"""
        target = policy.get('target')
        params = policy.get('parameters', {})
        
        logger.info(f"Applying QoS policy to {target}: {params}")
        
        # Check if target is ESP32 device (uses different message format)
        if 'esp32' in target.lower():
            control_message = {
                'command': 'SET_QOS',
                'qos': int(params.get('mqtt_qos', 1))
            }
        else:
            control_message = {
                'type': 'qos_update',
                'qos': params.get('mqtt_qos', 0),
                'reliable_delivery': params.get('reliable_delivery', False)
            }
        
        return self._send_control_message(target, control_message)
    
    def _apply_sample_rate_policy(self, policy: Dict) -> bool:
        """Apply sample rate policy to audio devices (ESP32)"""
        target = policy.get('target')
        params = policy.get('parameters', {})
        
        sample_rate = params.get('sample_rate', 16000)
        logger.info(f"Applying sample rate policy to {target}: {sample_rate} Hz")
        
        control_message = {
            'command': 'SET_SAMPLE_RATE',
            'sample_rate': int(sample_rate)
        }
        
        return self._send_control_message(target, control_message)
    
    def _apply_sampling_interval_policy(self, policy: Dict) -> bool:
        """Apply sampling interval policy to environmental sensors (MH-Z19 CO2 sensor)"""
        target = policy.get('target')
        params = policy.get('parameters', {})
        
        interval_seconds = params.get('interval_seconds', 10)
        logger.info(f"Applying sampling interval policy to {target}: {interval_seconds} seconds")
        
        # ESP32 MH-Z19 uses SET_PUBLISH_INTERVAL with interval_ms
        if 'esp32' in target.lower() or 'mhz19' in target.lower():
            control_message = {
                'command': 'SET_PUBLISH_INTERVAL',
                'interval_ms': int(interval_seconds) * 1000  # Convert seconds to ms
            }
        else:
            control_message = {
                'command': 'SET_SAMPLING_INTERVAL',
                'interval_seconds': int(interval_seconds)
            }
        
        return self._send_control_message(target, control_message)
    
    def _apply_device_control_policy(self, policy: Dict) -> bool:
        """Apply enable/disable/reset control to device"""
        target = policy.get('target')
        params = policy.get('parameters', {})
        
        command = params.get('command', 'ENABLE')
        logger.info(f"Applying device control to {target}: {command}")
        
        control_message = {
            'command': command
        }
        
        return self._send_control_message(target, control_message)
    
    def _apply_publish_interval_policy(self, policy: Dict) -> bool:
        """Apply publish interval policy to device"""
        target = policy.get('target')
        params = policy.get('parameters', {})
        
        interval_ms = params.get('interval_ms', 10000)
        logger.info(f"Applying publish interval policy to {target}: {interval_ms} ms")
        
        control_message = {
            'command': 'SET_PUBLISH_INTERVAL',
            'interval_ms': int(interval_ms)
        }
        
        return self._send_control_message(target, control_message)
    
    def _apply_audio_gain_policy(self, policy: Dict) -> bool:
        """Apply audio gain policy to audio devices"""
        target = policy.get('target')
        params = policy.get('parameters', {})
        
        gain = params.get('gain', 1.0)
        logger.info(f"Applying audio gain policy to {target}: {gain}x")
        
        control_message = {
            'command': 'SET_AUDIO_GAIN',
            'gain': float(gain)
        }
        
        return self._send_control_message(target, control_message)
    
    def _apply_camera_policy(self, policy: Dict) -> bool:
        """Apply camera control policy — resolution, quality, brightness, framerate, enable/disable."""
        target = policy.get('target')
        params = policy.get('parameters', {})
        policy_type = policy.get('policy_type', '')

        # Normalise resolution strings (e.g. '1080p' → 'HD', '480p' → 'VGA')
        RESOLUTION_MAP = {
            'qvga': 'QVGA', '240p': 'QVGA',
            'vga':  'VGA',  '480p': 'VGA',
            'svga': 'SVGA', '600p': 'SVGA',
            'xga':  'XGA',  '768p': 'XGA',
            'hd':   'HD',   '720p': 'HD',
            'sxga': 'SXGA', '960p': 'SXGA',
            'uxga': 'UXGA', '1080p': 'UXGA', 'full hd': 'UXGA',
        }
        QUALITY_PRESETS = {'high': 5, 'medium': 15, 'low': 35}

        control = {}

        if policy_type == 'camera_resolution':
            # Accept both parsed-intent key ('resolution_value') and policy-engine key ('resolution')
            raw_val = params.get('resolution_value') or params.get('resolution', '')
            raw = str(raw_val[0] if isinstance(raw_val, (list, tuple)) else raw_val).lower().strip()
            resolution = RESOLUTION_MAP.get(raw, raw.upper()) if raw else 'SVGA'
            control['resolution'] = resolution
            logger.info(f"Camera resolution → {resolution} on {target}")

        elif policy_type == 'camera_quality':
            if 'quality_preset' in params:
                preset = params['quality_preset']
                preset = preset[0] if isinstance(preset, (list, tuple)) else preset
                quality = QUALITY_PRESETS.get(str(preset).lower(), 15)
            elif 'quality' in params:
                # Policy-engine key
                quality = int(params['quality'])
                quality = max(0, min(63, quality))
            else:
                quality = int(params.get('quality_value', 15))
                quality = max(0, min(63, quality))
            control['quality'] = quality
            logger.info(f"Camera quality → {quality} on {target}")

        elif policy_type == 'camera_brightness':
            # Accept both 'brightness_value' (parsed) and 'brightness' (policy engine)
            brightness = int(params.get('brightness_value', params.get('brightness', 0)))
            brightness = max(-2, min(2, brightness))
            control['brightness'] = brightness
            logger.info(f"Camera brightness → {brightness} on {target}")

        elif policy_type == 'camera_framerate':
            if 'capture_interval_ms' in params:
                # Policy-engine key (pre-computed interval)
                interval_ms = int(params['capture_interval_ms'])
            elif 'framerate_value' in params:
                fps_val = params['framerate_value']
                fps = int(fps_val[0] if isinstance(fps_val, (list, tuple)) else fps_val)
                interval_ms = max(33, int(1000 / fps)) if fps > 0 else 1000
            else:
                interval_ms = int(params.get('capture_interval', 1000))
            control['capture_interval_ms'] = interval_ms
            logger.info(f"Camera interval → {interval_ms}ms on {target}")

        elif policy_type == 'camera_control':
            if 'enabled' in params:
                # Policy-engine key
                control['enabled'] = bool(params['enabled'])
            else:
                action = params.get('enable_camera') or params.get('camera_action', '')
                if isinstance(action, (list, tuple)):
                    action = action[0]
                control['enabled'] = 'enable' in str(action).lower() or str(action) == 'resume'
            logger.info(f"Camera control → {control} on {target}")

        if not control:
            logger.warning(f"Camera policy produced empty control message: {params}")
            return False

        # ESP32-CAM uses iot/{device_id}/control topic with plain JSON keys
        topic = f"iot/{target}/control"
        payload = json.dumps(control)
        result = self.client.publish(topic, payload, qos=1)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"Camera control sent → {topic}: {payload}")
            # Record metrics for Grafana visibility
            try:
                from metrics_exporter import record_device_enforcement, record_camera_state
                record_device_enforcement(policy_type, target, True)
                record_camera_state(target, **control)
            except ImportError:
                pass
            return True
        logger.error(f"Failed to send camera control: rc={result.rc}")
        try:
            from metrics_exporter import record_device_enforcement
            record_device_enforcement(policy_type, target, False)
        except ImportError:
            pass
        return False

    def _apply_device_config(self, policy: Dict) -> bool:
        """Apply device configuration"""
        target = policy.get('target')
        params = policy.get('parameters', {})
        
        logger.info(f"Applying device config to {target}: {params}")
        
        control_message = {
            'type': 'config_update',
            'sampling_rate': params.get('sampling_rate'),
            'enabled': params.get('enabled', True),
            'priority': params.get('priority', 'normal')
        }
        
        return self._send_control_message(target, control_message)
    
    def _send_control_message(self, target: str, message: Dict) -> bool:
        """Send control message to specific device"""
        if not self.connected:
            logger.error("Not connected to MQTT broker")
            return False
        
        try:
            # Topic routing per firmware:
            #   esp32-cam-1  → iot/  (camera_policy bypasses this method)
            #   esp32-audio-1 → iot/  (firmware subscribes iot/esp32-audio-1/control)
            #   esp32-mhz19-1 → imperium/devices/  (firmware subscribes both, primary is imperium/)
            #   mhz19-01      → imperium/devices/  
            #   esp32-env-1   → imperium/devices/
            #   node-X        → iot/
            target_lower = target.lower()
            if 'mhz19' in target_lower or 'env' in target_lower:
                topic = f"imperium/devices/{target}/control"
            else:
                topic = f"iot/{target}/control"
            
            payload = json.dumps(message)
            
            logger.info(f"Sending to topic: {topic}")
            result = self.client.publish(topic, payload, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Control message sent to {target}")
                try:
                    from metrics_exporter import record_device_enforcement
                    # Infer policy_type from message content
                    ptype = message.get('command', message.get('type', 'unknown'))
                    record_device_enforcement(ptype, target, True)
                except ImportError:
                    pass
                return True
            else:
                logger.error(f"Failed to send message: {result.rc}")
                try:
                    from metrics_exporter import record_device_enforcement
                    ptype = message.get('command', message.get('type', 'unknown'))
                    record_device_enforcement(ptype, target, False)
                except ImportError:
                    pass
                return False
                
        except Exception as e:
            logger.error(f"Error sending control message: {e}")
            return False
    
    def get_device_status(self, node_id: str) -> Dict[str, Any]:
        """Get status of specific device"""
        return self.device_status.get(node_id, {})
    
    def get_all_devices(self) -> Dict[str, Any]:
        """Get status of all devices"""
        return self.device_status


if __name__ == '__main__':
    # Test the device enforcer
    enforcer = DeviceEnforcer('localhost', 1883)
    
    try:
        enforcer.connect()
        
        test_policy = {
            'policy_id': 'test-1',
            'policy_type': 'qos_control',
            'target': 'node-1',
            'parameters': {
                'mqtt_qos': 2,
                'reliable_delivery': True
            }
        }
        
        logger.info("Testing device enforcer...")
        result = enforcer.apply_policy(test_policy)
        logger.info(f"Policy application result: {result}")
        
        time.sleep(2)
        
        devices = enforcer.get_all_devices()
        logger.info(f"Known devices: {list(devices.keys())}")
        
    finally:
        enforcer.disconnect()
