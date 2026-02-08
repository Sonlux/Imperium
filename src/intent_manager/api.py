#!/usr/bin/env python3
"""
Intent Manager - REST API for Intent Acquisition
Handles user intent submission and parsing
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from intent_manager.parser import IntentParser
from policy_engine.engine import PolicyEngine
from database import DatabaseManager
from auth import AuthManager, create_default_admin
from rate_limiter import RateLimiter
from intent_manager.auth_endpoints import init_auth_endpoints

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize security and database components
db_manager = DatabaseManager(db_path=os.getenv('DATABASE_PATH', 'data/imperium.db'))
auth_manager = AuthManager(db_manager=db_manager)
rate_limiter = RateLimiter()

# Create default admin user if not exists
try:
    create_default_admin(auth_manager)
except Exception as e:
    logger.warning(f"Could not create default admin: {e}")


class IntentManager:
    """Manages intent acquisition and validation"""
    
    def __init__(self, db_manager=None):
        self.intents = []  # In-memory cache for backwards compatibility
        self.parser = IntentParser()
        self.policy_engine = PolicyEngine()
        self.db_manager = db_manager or DatabaseManager()
        # Enforcement modules (set by main.py)
        self.device_enforcer = None
        self.network_enforcer = None
    
    def submit_intent(self, intent_data):
        """
        Accept and validate intent submission
        
        Args:
            intent_data: Dictionary containing intent information
            
        Returns:
            dict: Intent ID, status, and generated policies
        """
        intent_id = f"intent-{len(self.intents) + 1}-{int(datetime.now().timestamp())}"
        
        # Parse the intent
        description = intent_data.get('description', '')
        parsed = self.parser.parse(description)
        
        # Validate parsed intent
        is_valid, msg = self.parser.validate(parsed)
        
        if not is_valid:
            return {
                'id': intent_id,
                'status': 'invalid',
                'error': msg
            }
        
        # Generate policies
        policies = self.policy_engine.generate_policies(parsed)
        
        intent = {
            'id': intent_id,
            'timestamp': datetime.now().isoformat(),
            'description': description,
            'type': intent_data.get('type', parsed.get('type', 'general')),
            'parameters': intent_data.get('parameters', {}),
            'parsed': parsed,
            'policies': [p.to_dict() for p in policies],
            'status': 'active'
        }
        
        self.intents.append(intent)
        
        # Persist to database
        try:
            self.db_manager.add_intent(
                intent_id=intent_id,
                original_intent=description,
                parsed_intent=parsed,
                status='active'
            )
            
            # Save policies to database
            for policy in policies:
                policy_dict = policy.to_dict()
                self.db_manager.add_policy(
                    policy_id=policy_dict['policy_id'],
                    intent_id=intent_id,
                    policy_type=policy_dict['policy_type'],
                    parameters=policy_dict['parameters'],
                    status='pending'
                )
        except Exception as e:
            logger.warning(f"Failed to persist intent to database: {e}")
        
        # Enforce policies
        self._enforce_policies(policies, parsed)
        
        logger.info(f"Intent {intent_id} created with {len(policies)} policies")
        
        return intent
    
    def get_intent(self, intent_id):
        """Retrieve specific intent by ID"""
        for intent in self.intents:
            if intent['id'] == intent_id:
                return intent
        return None
    
    def _enforce_policies(self, policies, parsed):
        """Enforce generated policies via MQTT and network"""
        target_device = parsed.get('parameters', {}).get('target_device', '')
        
        # Normalize target (ensure node-X format for simulated nodes only, preserve esp32- prefix)
        if target_device and not target_device.startswith(('node-', 'esp32-')):
            target_device = f"node-{target_device}"
        
        for policy in policies:
            policy_dict = policy.to_dict()
            policy_type = policy_dict.get('policy_type', '')  # Fixed: was 'type'
            
            # Build enforcement policy
            enforce_policy = {
                'policy_type': policy_type,
                'target': target_device or policy_dict.get('target', ''),
                'parameters': policy_dict.get('parameters', {})  # Fixed: was 'config'
            }
            
            logger.info(f"Enforcing policy: {enforce_policy}")
            
            # Apply via device enforcer (MQTT) - includes ESP32 controls
            if self.device_enforcer and policy_type in ['qos_control', 'device_config', 'sample_rate', 'audio_gain', 'publish_interval']:
                try:
                    success = self.device_enforcer.apply_policy(enforce_policy)
                    logger.info(f"Device enforcement {'succeeded' if success else 'failed'}")
                except Exception as e:
                    logger.error(f"Device enforcement error: {e}")
            
            # Apply via network enforcer (tc)
            if self.network_enforcer and policy_type in ['bandwidth', 'latency', 'traffic_shaping']:
                try:
                    success = self.network_enforcer.apply_policy(enforce_policy)
                    logger.info(f"Network enforcement {'succeeded' if success else 'failed'}")
                except Exception as e:
                    logger.error(f"Network enforcement error: {e}")
    
    def list_intents(self):
        """List all submitted intents"""
        return self.intents


# Global intent manager instance
intent_manager = IntentManager(db_manager=db_manager)

# Initialize authentication endpoints
init_auth_endpoints(app, auth_manager, rate_limiter)


@app.route('/health', methods=['GET'])
@rate_limiter.limit('default')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'intent-manager',
        'features': {
            'authentication': True,
            'rate_limiting': True,
            'database': True
        }
    })


@app.route('/api/v1/intents', methods=['POST'])
@rate_limiter.limit('intents')
@auth_manager.require_auth
def submit_intent():
    """Submit a new intent (requires authentication)"""
    try:
        intent_data = request.get_json()
        
        if not intent_data:
            return jsonify({'error': 'No intent data provided'}), 400
        
        if 'description' not in intent_data:
            return jsonify({'error': 'Intent description is required'}), 400
        
        intent = intent_manager.submit_intent(intent_data)
        
        if intent.get('status') == 'invalid':
            return jsonify({
                'success': False,
                'intent': intent
            }), 400
        
        return jsonify({
            'success': True,
            'intent': intent
        }), 201
        
    except Exception as e:
        logger.error(f"Error submitting intent: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/intents', methods=['GET'])
@rate_limiter.limit('default')
@auth_manager.require_auth
def list_intents():
    """List all intents (requires authentication)"""
    # Try to get from database first
    try:
        db_intents = intent_manager.db_manager.get_all_intents(limit=100)
        if db_intents:
            return jsonify({'intents': db_intents, 'count': len(db_intents)})
    except Exception as e:
        logger.warning(f"Failed to retrieve from database: {e}")
    
    # Fall back to in-memory cache
    intents = intent_manager.list_intents()
    return jsonify({'intents': intents, 'count': len(intents)})


@app.route('/api/v1/intents/<intent_id>', methods=['GET'])
@rate_limiter.limit('default')
@auth_manager.require_auth
def get_intent(intent_id):
    """Get specific intent (requires authentication)"""
    # Try database first
    try:
        db_intent = intent_manager.db_manager.get_intent(intent_id)
        if db_intent:
            return jsonify({'intent': db_intent})
    except Exception as e:
        logger.warning(f"Failed to retrieve from database: {e}")
    
    # Fall back to in-memory
    intent = intent_manager.get_intent(intent_id)
    
    if intent:
        return jsonify({'intent': intent})
    else:
        return jsonify({'error': 'Intent not found'}), 404


@app.route('/api/v1/policies', methods=['GET'])
@rate_limiter.limit('default')
@auth_manager.require_auth
def list_policies():
    """List all generated policies (requires authentication)"""
    # Try database first
    try:
        db_policies = intent_manager.db_manager.get_all_policies(limit=100)
        if db_policies:
            return jsonify({'policies': db_policies, 'count': len(db_policies)})
    except Exception as e:
        logger.warning(f"Failed to retrieve from database: {e}")
    
    # Fall back to in-memory
    policies = intent_manager.policy_engine.get_policies()
    return jsonify({'policies': policies, 'count': len(policies)})


if __name__ == '__main__':
    logger.info("Starting Intent Manager API on port 5000...")
    logger.info("Endpoints available:")
    logger.info("  POST   /api/v1/intents - Submit new intent")
    logger.info("  GET    /api/v1/intents - List all intents")
    logger.info("  GET    /api/v1/intents/<id> - Get specific intent")
    logger.info("  GET    /api/v1/policies - List all policies")
    logger.info("  GET    /health - Health check")
    app.run(host='0.0.0.0', port=5000, debug=True)
