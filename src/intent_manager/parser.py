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
            ],
            'sample_rate': [
                (r'(?:set\s+)?sample\s*rate\s+(?:to\s+)?(\d+)\s*(?:hz|khz)?', 'sample_rate'),
                (r'(?:change|reduce|increase)\s+sampling\s+(?:rate\s+)?(?:to\s+)?(\d+)', 'sample_rate'),
                (r'audio\s+(?:sample\s*)?rate\s+(\d+)', 'sample_rate'),
                (r'(\d+)\s*(?:hz|khz)\s+(?:sample|sampling|audio)', 'sample_rate')
            ],
            'device_control': [
                (r'(?:enable|start|activate)\s+(?:device\s+)?(\S+)', 'enable_device'),
                (r'(?:disable|stop|deactivate)\s+(?:device\s+)?(\S+)', 'disable_device'),
                (r'reset\s+(?:device\s+)?(\S+)', 'reset_device')
            ],
            'publish_interval': [
                (r'(?:set\s+)?(?:publish|telemetry|reporting)\s+(?:interval|rate)\s+(?:to\s+)?(\d+)\s*(?:ms|seconds?|s)?', 'interval_value'),
                (r'(?:send|report)\s+(?:data|telemetry)\s+every\s+(\d+)\s*(?:ms|seconds?|s)?', 'interval_value'),
                (r'(?:reduce|increase)\s+(?:publish|telemetry)\s+(?:frequency|rate)?\s*(?:to\s+)?(\d+)', 'interval_value')
            ],
            'audio_gain': [
                (r'(?:set\s+)?(?:audio\s+)?gain\s+(?:to\s+)?(\d+\.?\d*)[x%]?', 'gain_value'),
                (r'(?:amplify|boost)\s+(?:audio\s+)?(?:by\s+)?(\d+\.?\d*)[x%]?', 'gain_value'),
                (r'(?:reduce|lower|decrease)\s+(?:audio\s+)?(?:volume|level|gain)\s+(?:to\s+)?(\d+\.?\d*)', 'gain_value'),
                (r'(?:set\s+)?audio\s+(?:volume|level)\s+(?:to\s+)?(\d+\.?\d*)', 'gain_value')
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
        
        # Extract ESP32 audio device targets
        esp_match = re.search(r'esp32[-_]?(audio[-_]?\d*|\d+)', intent_lower)
        if esp_match:
            parsed['parameters']['target_device'] = f"esp32-audio-{esp_match.group(1).replace('audio-', '').replace('audio', '1')}"
        
        # Handle 'for X' pattern for device targeting
        for_match = re.search(r'for\s+(esp32[-\w]*|node[-\w]*|\S+[-_]\d+)', intent_lower)
        if for_match and 'target_device' not in parsed['parameters']:
            parsed['parameters']['target_device'] = for_match.group(1)
        
        logger.info(f"Parsed intent: {parsed}")
        return parsed
    
    def _determine_type(self, intent_description: str) -> str:
        """Determine the primary intent type"""
        # Check QoS first before audio gain (to avoid 'level' keyword collision)
        if any(word in intent_description for word in ['qos', 'quality of service', 'reliable delivery']):
            return 'qos'
        elif any(word in intent_description for word in ['sample rate', 'sampling', 'audio rate', 'khz', ' hz']):
            return 'sample_rate'
        elif any(word in intent_description for word in ['gain', 'amplify', 'boost', 'audio volume', 'audio level']):
            return 'audio_gain'
        elif any(word in intent_description for word in ['publish interval', 'telemetry rate', 'telemetry', 'reporting', 'send data', 'report every', 'report telemetry']):
            return 'publish_interval'
        elif any(word in intent_description for word in ['enable', 'disable', 'start', 'stop', 'activate', 'deactivate', 'reset']):
            return 'device_control'
        elif any(word in intent_description for word in ['priority', 'prioritize', 'critical']):
            return 'priority'
        elif any(word in intent_description for word in ['bandwidth', 'throttle', 'limit']):
            return 'bandwidth'
        elif any(word in intent_description for word in ['latency', 'delay', 'response']):
            return 'latency'
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
