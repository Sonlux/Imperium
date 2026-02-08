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
    SAMPLE_RATE = "sample_rate"
    DEVICE_CONTROL = "device_control"
    PUBLISH_INTERVAL = "publish_interval"
    AUDIO_GAIN = "audio_gain"


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
        
        elif intent_type == 'device_control':
            policies.extend(self._generate_device_control_policies(parameters))
        
        elif intent_type == 'publish_interval':
            policies.extend(self._generate_publish_interval_policies(parameters))
        
        elif intent_type == 'audio_gain':
            policies.extend(self._generate_audio_gain_policies(parameters))
        
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
            value, unit = params['bandwidth_limit'][0], params['bandwidth_limit'][1] if len(params['bandwidth_limit']) > 1 else 'mbps'
            bandwidth_limit = f"{value}{unit}"
        elif 'throttle' in params:
            bandwidth_limit = f"{params['throttle'][1]}mbps"
        
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
        """Generate latency reduction policies"""
        policies = []
        target_device = params.get('target_device', 'all')
        
        # Traffic prioritization for low latency
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
    
    def _get_next_policy_id(self) -> str:
        """Generate unique policy ID"""
        self.policy_counter += 1
        return f"policy-{self.policy_counter}"
    
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
