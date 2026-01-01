# Imperium - Test Suite

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from intent_manager.parser import IntentParser
from policy_engine.engine import PolicyEngine


class TestIntentParser:
    """Test intent parsing functionality"""
    
    def setup_method(self):
        self.parser = IntentParser()
    
    def test_parse_priority_intent(self):
        """Test parsing priority intent"""
        intent = "Prioritize device node-1"
        result = self.parser.parse(intent)
        
        assert result['type'] == 'priority'
        assert 'target_device' in result['parameters']
        assert result['parameters']['target_device'] == '1'
    
    def test_parse_bandwidth_intent(self):
        """Test parsing bandwidth intent"""
        intent = "Limit bandwidth to 100 mbps"
        result = self.parser.parse(intent)
        
        assert result['type'] == 'bandwidth'
        assert 'bandwidth_limit' in result['parameters']
    
    def test_parse_latency_intent(self):
        """Test parsing latency intent"""
        intent = "Reduce latency to 50ms"
        result = self.parser.parse(intent)
        
        assert result['type'] == 'latency'
        assert 'latency_target' in result['parameters']
    
    def test_validate_valid_intent(self):
        """Test validation of valid intent"""
        intent = "Prioritize device node-1"
        parsed = self.parser.parse(intent)
        is_valid, msg = self.parser.validate(parsed)
        
        assert is_valid is True
        assert msg == "Valid"


class TestPolicyEngine:
    """Test policy generation functionality"""
    
    def setup_method(self):
        self.engine = PolicyEngine()
    
    def test_generate_priority_policies(self):
        """Test priority policy generation"""
        parsed_intent = {
            'type': 'priority',
            'parameters': {
                'target_device': 'node-1'
            }
        }
        
        policies = self.engine.generate_policies(parsed_intent)
        
        assert len(policies) > 0
        assert any(p.policy_type.value == 'traffic_shaping' for p in policies)
        assert any(p.policy_type.value == 'routing_priority' for p in policies)
    
    def test_generate_bandwidth_policies(self):
        """Test bandwidth policy generation"""
        parsed_intent = {
            'type': 'bandwidth',
            'parameters': {
                'target_device': 'node-2',
                'bandwidth_limit': ('100', 'mbps')
            }
        }
        
        policies = self.engine.generate_policies(parsed_intent)
        
        assert len(policies) > 0
        assert any(p.policy_type.value == 'bandwidth_limit' for p in policies)
    
    def test_policy_to_dict(self):
        """Test policy serialization"""
        parsed_intent = {
            'type': 'latency',
            'parameters': {
                'target_device': 'node-3'
            }
        }
        
        policies = self.engine.generate_policies(parsed_intent)
        policy_dict = policies[0].to_dict()
        
        assert 'policy_id' in policy_dict
        assert 'policy_type' in policy_dict
        assert 'target' in policy_dict
        assert 'parameters' in policy_dict
        assert 'priority' in policy_dict


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
