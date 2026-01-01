#!/usr/bin/env python3
"""
Intent Parser - Converts high-level intents into structured parameters
"""
import re
import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntentParser:
    """Parse and extract parameters from intent descriptions"""
    
    def __init__(self):
        self.intent_patterns = {
            'priority': [
                (r'prioritize\s+(?:device|node)\s+(\S+)', 'device_id'),
                (r'high\s+priority\s+(?:for\s+)?(\S+)', 'device_id'),
                (r'priority\s+(\d+)', 'priority_level')
            ],
            'bandwidth': [
                (r'limit\s+bandwidth\s+(?:to\s+)?(\d+)\s*(mbps|kbps|gbps)?', 'bandwidth_limit'),
                (r'allocate\s+(\d+)\s*(mbps|kbps|gbps)?\s+(?:to|for)\s+(\S+)', 'bandwidth_allocation'),
                (r'throttle\s+(\S+)\s+(?:to\s+)?(\d+)', 'throttle')
            ],
            'latency': [
                (r'reduce\s+latency\s+(?:to\s+)?(\d+)\s*ms', 'latency_target'),
                (r'latency\s+(?:below|under)\s+(\d+)', 'latency_threshold'),
                (r'minimize\s+latency\s+(?:for\s+)?(\S+)?', 'low_latency')
            ],
            'qos': [
                (r'qos\s+(?:level\s+)?(\d+)', 'qos_level'),
                (r'quality\s+of\s+service\s+(\d+)', 'qos_level'),
                (r'reliable\s+delivery\s+(?:for\s+)?(\S+)', 'reliable_delivery')
            ]
        }
    
    def parse(self, intent_description: str) -> Dict[str, Any]:
        """
        Parse intent description and extract parameters
        
        Args:
            intent_description: Natural language or structured intent
            
        Returns:
            dict: Parsed parameters
        """
        intent_lower = intent_description.lower()
        parsed = {
            'original': intent_description,
            'type': self._determine_type(intent_lower),
            'parameters': {}
        }
        
        # Extract parameters based on patterns
        for intent_type, patterns in self.intent_patterns.items():
            for pattern, param_name in patterns:
                match = re.search(pattern, intent_lower)
                if match:
                    parsed['parameters'][param_name] = match.groups()
                    if intent_type not in parsed:
                        parsed[intent_type] = True
        
        # Extract device/node targets
        device_match = re.search(r'(?:device|node)[-_]?(\w+)', intent_lower)
        if device_match:
            parsed['parameters']['target_device'] = device_match.group(1)
        
        logger.info(f"Parsed intent: {parsed}")
        return parsed
    
    def _determine_type(self, intent_description: str) -> str:
        """Determine the primary intent type"""
        if any(word in intent_description for word in ['priority', 'prioritize', 'critical']):
            return 'priority'
        elif any(word in intent_description for word in ['bandwidth', 'throttle', 'limit']):
            return 'bandwidth'
        elif any(word in intent_description for word in ['latency', 'delay', 'response']):
            return 'latency'
        elif any(word in intent_description for word in ['qos', 'quality', 'reliable']):
            return 'qos'
        else:
            return 'general'
    
    def validate(self, parsed_intent: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate parsed intent has necessary parameters
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if not parsed_intent.get('type'):
            return False, "Unable to determine intent type"
        
        if not parsed_intent.get('parameters'):
            return False, "No actionable parameters extracted"
        
        return True, "Valid"


if __name__ == '__main__':
    # Test the parser
    parser = IntentParser()
    
    test_intents = [
        "Prioritize device node-1",
        "Limit bandwidth to 100 mbps for device node-2",
        "Reduce latency to 50ms",
        "Set QoS level 2 for critical devices"
    ]
    
    for intent in test_intents:
        print(f"\nIntent: {intent}")
        parsed = parser.parse(intent)
        print(f"Result: {parsed}")
        is_valid, msg = parser.validate(parsed)
        print(f"Valid: {is_valid} - {msg}")
