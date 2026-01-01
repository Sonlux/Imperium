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

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntentManager:
    """Manages intent acquisition and validation"""
    
    def __init__(self):
        self.intents = []
        self.parser = IntentParser()
        self.policy_engine = PolicyEngine()
    
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
        logger.info(f"Intent {intent_id} created with {len(policies)} policies")
        
        return intent
    
    def get_intent(self, intent_id):
        """Retrieve specific intent by ID"""
        for intent in self.intents:
            if intent['id'] == intent_id:
                return intent
        return None
    
    def list_intents(self):
        """List all submitted intents"""
        return self.intents


# Global intent manager instance
intent_manager = IntentManager()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'intent-manager'})


@app.route('/api/v1/intents', methods=['POST'])
def submit_intent():
    """Submit a new intent"""
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
def list_intents():
    """List all intents"""
    intents = intent_manager.list_intents()
    return jsonify({'intents': intents, 'count': len(intents)})


@app.route('/api/v1/intents/<intent_id>', methods=['GET'])
def get_intent(intent_id):
    """Get specific intent"""
    intent = intent_manager.get_intent(intent_id)
    
    if intent:
        return jsonify({'intent': intent})
    else:
        return jsonify({'error': 'Intent not found'}), 404


@app.route('/api/v1/policies', methods=['GET'])
def list_policies():
    """List all generated policies"""
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
