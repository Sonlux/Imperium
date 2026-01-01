#!/usr/bin/env python3
"""
Feedback Loop - Monitors network performance and adjusts policies
Queries Prometheus for metrics and triggers policy adjustments
"""
import requests
import logging
import time
from typing import Dict, Any, List
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeedbackEngine:
    """Monitors performance and provides feedback for policy adjustment"""
    
    def __init__(self, prometheus_url='http://localhost:9090'):
        self.prometheus_url = prometheus_url
        self.intent_goals = {}
        self.metrics_history = []
    
    def register_intent(self, intent_id: str, goals: Dict[str, Any]):
        """
        Register intent goals for monitoring
        
        Args:
            intent_id: Intent identifier
            goals: Dictionary of performance goals (latency, throughput, etc.)
        """
        self.intent_goals[intent_id] = {
            'goals': goals,
            'registered_at': datetime.now().isoformat(),
            'satisfied': False
        }
        logger.info(f"Registered intent {intent_id} with goals: {goals}")
    
    def query_prometheus(self, query: str) -> Dict:
        """
        Query Prometheus for metrics
        
        Args:
            query: PromQL query string
            
        Returns:
            Query result
        """
        try:
            url = f"{self.prometheus_url}/api/v1/query"
            params = {'query': query}
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'success':
                return data['data']
            else:
                logger.error(f"Prometheus query failed: {data}")
                return {}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to query Prometheus: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error querying Prometheus: {e}")
            return {}
    
    def get_latency_metrics(self, node_id: str = None) -> float:
        """Get current latency metrics"""
        if node_id:
            query = f'iot_latency_ms{{node_id="{node_id}"}}'
        else:
            query = 'avg(iot_latency_ms)'
        
        result = self.query_prometheus(query)
        
        if result and result.get('result'):
            return float(result['result'][0]['value'][1])
        
        return 0.0
    
    def get_throughput_metrics(self, node_id: str = None) -> float:
        """Get current throughput metrics"""
        if node_id:
            query = f'rate(iot_messages_sent_total{{node_id="{node_id}"}}[1m])'
        else:
            query = 'sum(rate(iot_messages_sent_total[1m]))'
        
        result = self.query_prometheus(query)
        
        if result and result.get('result'):
            return float(result['result'][0]['value'][1])
        
        return 0.0
    
    def get_bandwidth_usage(self, node_id: str = None) -> float:
        """Get current bandwidth usage"""
        if node_id:
            query = f'iot_bandwidth_bytes{{node_id="{node_id}"}}'
        else:
            query = 'sum(iot_bandwidth_bytes)'
        
        result = self.query_prometheus(query)
        
        if result and result.get('result'):
            return float(result['result'][0]['value'][1])
        
        return 0.0
    
    def check_intent_satisfaction(self, intent_id: str) -> Dict[str, Any]:
        """
        Check if intent goals are being met
        
        Args:
            intent_id: Intent identifier
            
        Returns:
            Dictionary with satisfaction status and metrics
        """
        if intent_id not in self.intent_goals:
            logger.warning(f"Intent {intent_id} not registered")
            return {'satisfied': False, 'error': 'Intent not registered'}
        
        intent = self.intent_goals[intent_id]
        goals = intent['goals']
        
        # Collect current metrics
        current_metrics = {
            'latency': self.get_latency_metrics(),
            'throughput': self.get_throughput_metrics(),
            'bandwidth': self.get_bandwidth_usage(),
            'timestamp': datetime.now().isoformat()
        }
        
        # Check each goal
        satisfaction = {
            'intent_id': intent_id,
            'satisfied': True,
            'metrics': current_metrics,
            'goals': goals,
            'violations': []
        }
        
        # Check latency goal
        if 'max_latency' in goals:
            if current_metrics['latency'] > goals['max_latency']:
                satisfaction['satisfied'] = False
                satisfaction['violations'].append({
                    'metric': 'latency',
                    'expected': goals['max_latency'],
                    'actual': current_metrics['latency']
                })
        
        # Check throughput goal
        if 'min_throughput' in goals:
            if current_metrics['throughput'] < goals['min_throughput']:
                satisfaction['satisfied'] = False
                satisfaction['violations'].append({
                    'metric': 'throughput',
                    'expected': goals['min_throughput'],
                    'actual': current_metrics['throughput']
                })
        
        # Check bandwidth goal
        if 'max_bandwidth' in goals:
            if current_metrics['bandwidth'] > goals['max_bandwidth']:
                satisfaction['satisfied'] = False
                satisfaction['violations'].append({
                    'metric': 'bandwidth',
                    'expected': goals['max_bandwidth'],
                    'actual': current_metrics['bandwidth']
                })
        
        # Store in history
        self.metrics_history.append(current_metrics)
        
        # Update intent status
        self.intent_goals[intent_id]['satisfied'] = satisfaction['satisfied']
        
        logger.info(f"Intent {intent_id} satisfaction: {satisfaction['satisfied']}")
        if satisfaction['violations']:
            logger.warning(f"Violations detected: {satisfaction['violations']}")
        
        return satisfaction
    
    def recommend_adjustments(self, intent_id: str) -> List[Dict[str, Any]]:
        """
        Recommend policy adjustments based on current metrics
        
        Args:
            intent_id: Intent identifier
            
        Returns:
            List of recommended policy adjustments
        """
        satisfaction = self.check_intent_satisfaction(intent_id)
        
        if satisfaction['satisfied']:
            logger.info(f"Intent {intent_id} is satisfied, no adjustments needed")
            return []
        
        recommendations = []
        
        for violation in satisfaction['violations']:
            metric = violation['metric']
            
            if metric == 'latency':
                # Recommend higher priority or better QoS
                recommendations.append({
                    'action': 'increase_priority',
                    'reason': f"Latency {violation['actual']} exceeds goal {violation['expected']}",
                    'parameters': {
                        'priority': 'high',
                        'qos': 2
                    }
                })
            
            elif metric == 'throughput':
                # Recommend increased bandwidth allocation
                recommendations.append({
                    'action': 'increase_bandwidth',
                    'reason': f"Throughput {violation['actual']} below goal {violation['expected']}",
                    'parameters': {
                        'bandwidth': f"{int(violation['expected'] * 1.5)}mbps"
                    }
                })
            
            elif metric == 'bandwidth':
                # Recommend throttling
                recommendations.append({
                    'action': 'throttle_bandwidth',
                    'reason': f"Bandwidth {violation['actual']} exceeds goal {violation['expected']}",
                    'parameters': {
                        'bandwidth': f"{int(violation['expected'])}mbps"
                    }
                })
        
        logger.info(f"Generated {len(recommendations)} adjustment recommendations")
        return recommendations
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of current metrics across all intents"""
        return {
            'intents': len(self.intent_goals),
            'satisfied': sum(1 for i in self.intent_goals.values() if i['satisfied']),
            'current_metrics': {
                'latency': self.get_latency_metrics(),
                'throughput': self.get_throughput_metrics(),
                'bandwidth': self.get_bandwidth_usage()
            },
            'history_size': len(self.metrics_history)
        }


if __name__ == '__main__':
    # Test feedback engine
    engine = FeedbackEngine()
    
    # Register test intent
    engine.register_intent('test-1', {
        'max_latency': 100,
        'min_throughput': 10,
        'max_bandwidth': 1000000
    })
    
    # Check satisfaction
    satisfaction = engine.check_intent_satisfaction('test-1')
    print(f"\nIntent satisfaction: {satisfaction}")
    
    # Get recommendations
    recommendations = engine.recommend_adjustments('test-1')
    print(f"\nRecommendations: {recommendations}")
    
    # Get summary
    summary = engine.get_metrics_summary()
    print(f"\nMetrics summary: {summary}")
