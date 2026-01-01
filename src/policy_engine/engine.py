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
