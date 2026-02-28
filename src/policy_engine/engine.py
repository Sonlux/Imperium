#!/usr/bin/env python3
"""
Policy Engine - Transforms intents into actionable policies
"""
import logging
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PolicyType(Enum):
    """Types of policies that can be generated"""
    TRAFFIC_SHAPING = "traffic_shaping"
    QOS_CONTROL = "qos_control"
    ROUTING_PRIORITY = "routing_priority"
    DEVICE_CONFIG = "device_config"
    BANDWIDTH_LIMIT = "bandwidth_limit"
    LATENCY_CONTROL = "latency_control"
    SAMPLE_RATE = "sample_rate"
    SAMPLING_INTERVAL = "sampling_interval"
    DEVICE_CONTROL = "device_control"
    PUBLISH_INTERVAL = "publish_interval"
    AUDIO_GAIN = "audio_gain"
    CAMERA_RESOLUTION = "camera_resolution"
    CAMERA_QUALITY = "camera_quality"
    CAMERA_BRIGHTNESS = "camera_brightness"
    CAMERA_FRAMERATE = "camera_framerate"
    CAMERA_CONTROL = "camera_control"


@dataclass
class Policy:
    """Represents a single network policy"""
    policy_id: str
    policy_type: PolicyType
    target: str
    parameters: Dict[str, Any]
    priority: int = 5
    
    def to_dict(self):
        return {
            'policy_id': self.policy_id,
            'policy_type': self.policy_type.value,
            'target': self.target,
            'parameters': self.parameters,
            'priority': self.priority
        }


class PolicyEngine:
    """Generates policies from parsed intents"""
    
    def __init__(self):
        self.policies = []
        self.policy_counter = 0
    
    def generate_policies(self, parsed_intent: Dict[str, Any]) -> List[Policy]:
        """
        Generate policies from parsed intent
        
        Args:
            parsed_intent: Output from IntentParser
            
        Returns:
            List of Policy objects
        """
        policies = []
        intent_type = parsed_intent.get('type')
        parameters = parsed_intent.get('parameters', {})
        
        # Generate policies based on intent type
        if intent_type == 'priority':
            policies.extend(self._generate_priority_policies(parameters))
        
        elif intent_type == 'bandwidth':
            policies.extend(self._generate_bandwidth_policies(parameters))
        
        elif intent_type == 'latency':
            policies.extend(self._generate_latency_policies(parameters))
        
        elif intent_type == 'qos':
            policies.extend(self._generate_qos_policies(parameters))
        
        elif intent_type == 'sample_rate':
            policies.extend(self._generate_sample_rate_policies(parameters))
        
        elif intent_type == 'sampling_interval':
            policies.extend(self._generate_sampling_interval_policies(parameters))
        
        elif intent_type == 'device_control':
            policies.extend(self._generate_device_control_policies(parameters))
        
        elif intent_type == 'publish_interval':
            policies.extend(self._generate_publish_interval_policies(parameters))
        
        elif intent_type == 'audio_gain':
            policies.extend(self._generate_audio_gain_policies(parameters))
        
        elif intent_type == 'camera_resolution':
            policies.extend(self._generate_camera_resolution_policies(parameters))
        
        elif intent_type == 'camera_quality':
            policies.extend(self._generate_camera_quality_policies(parameters))
        
        elif intent_type == 'camera_brightness':
            policies.extend(self._generate_camera_brightness_policies(parameters))
        
        elif intent_type == 'camera_framerate':
            policies.extend(self._generate_camera_framerate_policies(parameters))
        
        elif intent_type == 'camera_control':
            policies.extend(self._generate_camera_control_policies(parameters))
        
        # Store generated policies
        self.policies.extend(policies)
        
        logger.info(f"Generated {len(policies)} policies from intent")
        return policies
    
    def _generate_priority_policies(self, params: Dict) -> List[Policy]:
        """Generate priority-based policies"""
        policies = []
        target_device = params.get('target_device', params.get('device_id', ['unknown'])[0])
        
        # Traffic shaping policy
        policy = Policy(
            policy_id=self._get_next_policy_id(),
            policy_type=PolicyType.TRAFFIC_SHAPING,
            target=target_device,
            parameters={
                'class': 'high_priority',
                'rate': '100mbit',
                'ceil': '200mbit',
                'burst': '32k'
            },
            priority=9
        )
        policies.append(policy)
        
        # Routing priority
        routing_policy = Policy(
            policy_id=self._get_next_policy_id(),
            policy_type=PolicyType.ROUTING_PRIORITY,
            target=target_device,
            parameters={
                'tos': '0x10',
                'priority': 'high'
            },
            priority=8
        )
        policies.append(routing_policy)
        
        return policies
    
    def _generate_bandwidth_policies(self, params: Dict) -> List[Policy]:
        """Generate bandwidth control policies"""
        policies = []
        target_device = params.get('target_device', 'all')
        
        # Extract bandwidth limit
        bandwidth_limit = None
        if 'bandwidth_limit' in params:
            value = params['bandwidth_limit'][0]
            unit = params['bandwidth_limit'][1] if len(params['bandwidth_limit']) > 1 and params['bandwidth_limit'][1] else 'mbit'
            # Normalise: mbps→mbit, kbps→kbit, gbps→gbit
            unit = unit.replace('bps', 'bit') if unit.endswith('bps') else unit
            bandwidth_limit = f"{value}{unit}"
        elif 'throttle' in params:
            bandwidth_limit = f"{params['throttle'][1]}mbit"
        
        if bandwidth_limit:
            policy = Policy(
                policy_id=self._get_next_policy_id(),
                policy_type=PolicyType.BANDWIDTH_LIMIT,
                target=target_device,
                parameters={
                    'rate': bandwidth_limit,
                    'ceil': bandwidth_limit,
                    'burst': '15k'
                },
                priority=7
            )
            policies.append(policy)
        
        return policies
    
    def _generate_latency_policies(self, params: Dict) -> List[Policy]:
        """Generate latency control policies.
        
        Two modes:
          1. 'latency_inject' → netem delay (adds artificial latency)
          2. 'latency_target' / 'low_latency' → traffic shaping for low latency
        """
        policies = []
        target_device = params.get('target_device', 'all')

        # Mode 1: user wants to inject/set a specific delay
        if 'latency_inject' in params:
            delay_ms = params['latency_inject']
            if isinstance(delay_ms, (list, tuple)):
                delay_ms = delay_ms[0]
            delay_ms = int(delay_ms)
            policy = Policy(
                policy_id=self._get_next_policy_id(),
                policy_type=PolicyType.LATENCY_CONTROL,
                target=target_device,
                parameters={
                    'delay': f'{delay_ms}ms',
                    'jitter': f'{max(1, delay_ms // 10)}ms',
                },
                priority=8
            )
            policies.append(policy)
            return policies

        # Mode 2: traffic prioritisation for low latency
        policy = Policy(
            policy_id=self._get_next_policy_id(),
            policy_type=PolicyType.TRAFFIC_SHAPING,
            target=target_device,
            parameters={
                'class': 'low_latency',
                'netem_delay': '0ms',
                'priority': 'express',
                'queue': 'fq_codel'
            },
            priority=9
        )
        policies.append(policy)
        
        return policies
    
    def _generate_qos_policies(self, params: Dict) -> List[Policy]:
        """Generate QoS policies"""
        policies = []
        target_device = params.get('target_device', 'all')
        qos_level = params.get('qos_level', [1])[0]
        
        policy = Policy(
            policy_id=self._get_next_policy_id(),
            policy_type=PolicyType.QOS_CONTROL,
            target=target_device,
            parameters={
                'mqtt_qos': qos_level,
                'reliable_delivery': True if qos_level in [1, 2] else False,
                'retain': True
            },
            priority=6
        )
        policies.append(policy)
        
        return policies
    
    def _generate_sample_rate_policies(self, params: Dict) -> List[Policy]:
        """Generate sample rate policies for audio devices"""
        policies = []
        target_device = params.get('target_device', 'esp32-audio-1')
        
        # Extract sample rate value
        sample_rate = 16000  # Default
        if 'sample_rate' in params:
            rate_tuple = params['sample_rate']
            rate_str = rate_tuple[0] if isinstance(rate_tuple, tuple) else str(rate_tuple)
            rate_val = int(rate_str)
            # Handle kHz notation
            if rate_val < 1000:
                rate_val *= 1000
            sample_rate = rate_val
        
        # Validate sample rate (supported: 8000, 16000, 44100, 48000)
        valid_rates = [8000, 16000, 44100, 48000]
        if sample_rate not in valid_rates:
            # Find closest valid rate
            sample_rate = min(valid_rates, key=lambda x: abs(x - sample_rate))
            logger.warning(f"Adjusted sample rate to nearest valid value: {sample_rate}")
        
        policy = Policy(
            policy_id=self._get_next_policy_id(),
            policy_type=PolicyType.SAMPLE_RATE,
            target=target_device,
            parameters={
                'sample_rate': sample_rate,
                'command': 'SET_SAMPLE_RATE'
            },
            priority=7
        )
        policies.append(policy)
        
        return policies
    
    def _generate_sampling_interval_policies(self, params: Dict) -> List[Policy]:
        """Generate sampling interval policies for environmental sensors (CO2, temp, humidity)"""
        policies = []
        target_device = params.get('target_device', 'mhz19-01')
        
        # Extract interval value in seconds
        interval_seconds = 10  # Default
        if 'interval_seconds' in params:
            interval_tuple = params['interval_seconds']
            interval_str = interval_tuple[0] if isinstance(interval_tuple, tuple) else str(interval_tuple)
            interval_seconds = int(interval_str)
        
        # Validate interval (min 2 seconds for MH-Z19, max 3600)
        interval_seconds = max(2, min(3600, interval_seconds))
        
        policy = Policy(
            policy_id=self._get_next_policy_id(),
            policy_type=PolicyType.SAMPLING_INTERVAL,
            target=target_device,
            parameters={
                'interval_seconds': interval_seconds,
                'command': 'SET_SAMPLING_INTERVAL'
            },
            priority=7
        )
        policies.append(policy)
        
        return policies
    
    def _generate_device_control_policies(self, params: Dict) -> List[Policy]:
        """Generate device enable/disable/reset policies"""
        policies = []
        
        # Determine command type
        command = 'ENABLE'
        if 'enable_device' in params:
            command = 'ENABLE'
            target = params['enable_device'][0] if isinstance(params['enable_device'], tuple) else params.get('target_device', 'unknown')
        elif 'disable_device' in params:
            command = 'DISABLE'
            target = params['disable_device'][0] if isinstance(params['disable_device'], tuple) else params.get('target_device', 'unknown')
        elif 'reset_device' in params:
            command = 'RESET'
            target = params['reset_device'][0] if isinstance(params['reset_device'], tuple) else params.get('target_device', 'unknown')
        else:
            target = params.get('target_device', 'unknown')
        
        policy = Policy(
            policy_id=self._get_next_policy_id(),
            policy_type=PolicyType.DEVICE_CONTROL,
            target=target,
            parameters={
                'command': command
            },
            priority=8
        )
        policies.append(policy)
        
        return policies
    
    def _generate_publish_interval_policies(self, params: Dict) -> List[Policy]:
        """Generate publish interval policies"""
        policies = []
        target = params.get('target_device', 'esp32-audio-1')
        
        # Extract interval value (could be in seconds or ms)
        interval_value = params.get('interval_value', ('10',))
        if isinstance(interval_value, tuple):
            interval_value = interval_value[0]
        
        # Convert to milliseconds
        try:
            interval_ms = int(interval_value)
            # If value > 1000, assume it's already in ms, else convert from seconds
            if interval_ms <= 60:
                interval_ms = interval_ms * 1000
            # Clamp to valid range (1-60 seconds)
            interval_ms = max(1000, min(60000, interval_ms))
        except (ValueError, TypeError):
            interval_ms = 10000  # Default 10 seconds
        
        policy = Policy(
            policy_id=self._get_next_policy_id(),
            policy_type=PolicyType.PUBLISH_INTERVAL,
            target=target,
            parameters={
                'interval_ms': interval_ms,
                'command': 'SET_PUBLISH_INTERVAL'
            },
            priority=5
        )
        policies.append(policy)
        
        return policies
    
    def _generate_audio_gain_policies(self, params: Dict) -> List[Policy]:
        """Generate audio gain policies"""
        policies = []
        target = params.get('target_device', 'esp32-audio-1')
        
        # Extract gain value
        gain_value = params.get('gain_value', ('1.0',))
        if isinstance(gain_value, tuple):
            gain_value = gain_value[0]
        
        # Convert to float and clamp to valid range (0.1-10x)
        try:
            gain = float(gain_value)
            gain = max(0.1, min(10.0, gain))
        except (ValueError, TypeError):
            gain = 1.0  # Default no gain
        
        policy = Policy(
            policy_id=self._get_next_policy_id(),
            policy_type=PolicyType.AUDIO_GAIN,
            target=target,
            parameters={
                'gain': gain,
                'command': 'SET_AUDIO_GAIN'
            },
            priority=5
        )
        policies.append(policy)
        
        return policies
    
    def _generate_camera_resolution_policies(self, params: Dict) -> List[Policy]:
        """Generate camera resolution control policies"""
        policies = []
        target = params.get('target_device', 'esp32-cam-1')
        
        # Extract resolution value
        resolution_value = params.get('resolution_value', ('SVGA',))[0] if params.get('resolution_value') else 'SVGA'
        
        # Normalize resolution format
        resolution_map = {
            'qvga': 'QVGA', '320x240': 'QVGA',
            'vga': 'VGA', '640x480': 'VGA',
            'svga': 'SVGA', '800x600': 'SVGA',
            'xga': 'XGA', '1024x768': 'XGA',
            'hd': 'HD', '1280x720': 'HD',
            'sxga': 'SXGA', '1280x1024': 'SXGA',
            'uxga': 'UXGA', '1600x1200': 'UXGA'
        }
        
        resolution = resolution_map.get(resolution_value.lower(), resolution_value.upper())
        
        policy = Policy(
            policy_id=self._get_next_policy_id(),
            policy_type=PolicyType.CAMERA_RESOLUTION,
            target=target,
            parameters={
                'resolution': resolution,
                'command': 'SET_RESOLUTION'
            },
            priority=5
        )
        policies.append(policy)
        
        return policies
    
    def _generate_camera_quality_policies(self, params: Dict) -> List[Policy]:
        """Generate camera quality control policies"""
        policies = []
        target = params.get('target_device', 'esp32-cam-1')
        
        # Extract quality value (0-63, lower is better for JPEG)
        quality_value = params.get('quality_value', (10,))[0] if params.get('quality_value') else 10
        
        # Handle quality presets
        if 'quality_preset' in params:
            preset = params['quality_preset'][0].lower()
            quality_map = {'high': 5, 'medium': 15, 'low': 30}
            quality_value = quality_map.get(preset, 10)
        
        try:
            quality = int(quality_value)
            quality = max(0, min(63, quality))  # Clamp to valid range
        except (ValueError, TypeError):
            quality = 10  # Default medium quality
        
        policy = Policy(
            policy_id=self._get_next_policy_id(),
            policy_type=PolicyType.CAMERA_QUALITY,
            target=target,
            parameters={
                'quality': quality,
                'command': 'SET_QUALITY'
            },
            priority=5
        )
        policies.append(policy)
        
        return policies
    
    def _generate_camera_brightness_policies(self, params: Dict) -> List[Policy]:
        """Generate camera brightness control policies"""
        policies = []
        target = params.get('target_device', 'esp32-cam-1')
        
        # Extract brightness value (-2 to 2)
        brightness_value = params.get('brightness_value', (0,))[0] if params.get('brightness_value') else 0
        
        try:
            brightness = int(brightness_value)
            brightness = max(-2, min(2, brightness))  # Clamp to valid range
        except (ValueError, TypeError):
            brightness = 0  # Default neutral
        
        policy = Policy(
            policy_id=self._get_next_policy_id(),
            policy_type=PolicyType.CAMERA_BRIGHTNESS,
            target=target,
            parameters={
                'brightness': brightness,
                'command': 'SET_BRIGHTNESS'
            },
            priority=5
        )
        policies.append(policy)
        
        return policies
    
    def _generate_camera_framerate_policies(self, params: Dict) -> List[Policy]:
        """Generate camera frame rate/capture interval control policies"""
        policies = []
        target = params.get('target_device', 'esp32-cam-1')
        
        # Extract frame rate or capture interval
        if 'framerate_value' in params:
            fps = int(params['framerate_value'][0])
            interval_ms = int(1000 / fps) if fps > 0 else 5000
        elif 'capture_interval' in params:
            interval = int(params['capture_interval'][0])
            # Determine if value is in seconds or milliseconds (assume seconds if < 100)
            interval_ms = interval * 1000 if interval < 100 else interval
        else:
            interval_ms = 5000  # Default 5 seconds
        
        # Clamp to valid range (100ms to 60000ms = 10 FPS to 1 frame per minute)
        interval_ms = max(100, min(60000, interval_ms))
        
        policy = Policy(
            policy_id=self._get_next_policy_id(),
            policy_type=PolicyType.CAMERA_FRAMERATE,
            target=target,
            parameters={
                'capture_interval_ms': interval_ms,
                'fps': round(1000 / interval_ms, 2),
                'command': 'SET_FRAMERATE'
            },
            priority=5
        )
        policies.append(policy)
        
        return policies
    
    def _generate_camera_control_policies(self, params: Dict) -> List[Policy]:
        """Generate camera enable/disable control policies"""
        policies = []
        target = params.get('target_device', 'esp32-cam-1')
        
        # Determine action
        if 'enable_camera' in params:
            enabled = True
            action = 'ENABLE_CAMERA'
        elif 'disable_camera' in params:
            enabled = False
            action = 'DISABLE_CAMERA'
        elif 'camera_action' in params:
            camera_action = params['camera_action'][0].lower()
            enabled = 'resume' in camera_action or 'start' in camera_action
            action = 'ENABLE_CAMERA' if enabled else 'DISABLE_CAMERA'
        else:
            enabled = True
            action = 'ENABLE_CAMERA'
        
        policy = Policy(
            policy_id=self._get_next_policy_id(),
            policy_type=PolicyType.CAMERA_CONTROL,
            target=target,
            parameters={
                'enabled': enabled,
                'command': action
            },
            priority=7
        )
        policies.append(policy)
        
        return policies
    
    def _get_next_policy_id(self) -> str:
        """Generate unique policy ID"""
        import uuid
        return f"policy-{uuid.uuid4().hex[:8]}"
    
    def get_policies(self) -> List[Dict]:
        """Return all generated policies"""
        return [p.to_dict() for p in self.policies]


if __name__ == '__main__':
    # Test policy engine
    engine = PolicyEngine()
    
    test_intent = {
        'type': 'priority',
        'parameters': {
            'target_device': 'node-1'
        }
    }
    
    policies = engine.generate_policies(test_intent)
    print(f"\nGenerated {len(policies)} policies:")
    for policy in policies:
        print(f"  - {policy.to_dict()}")
