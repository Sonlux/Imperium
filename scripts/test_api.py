#!/usr/bin/env python3
"""
Simple test script to verify the system is working
"""
import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_health():
    """Test health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_submit_intent():
    """Test intent submission"""
    print("\n=== Testing Intent Submission ===")
    
    test_intents = [
        {
            "description": "Prioritize device node-1",
            "type": "priority"
        },
        {
            "description": "Limit bandwidth to 100 mbps for node-2",
            "type": "bandwidth"
        },
        {
            "description": "Reduce latency to 50ms",
            "type": "latency"
        }
    ]
    
    intent_ids = []
    
    for intent_data in test_intents:
        print(f"\nSubmitting: {intent_data['description']}")
        response = requests.post(
            f"{BASE_URL}/api/v1/intents",
            json=intent_data
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            intent_id = result['intent']['id']
            intent_ids.append(intent_id)
            print(f"Intent ID: {intent_id}")
            print(f"Policies generated: {len(result['intent']['policies'])}")
            
            for policy in result['intent']['policies']:
                print(f"  - {policy['policy_type']}: {policy['target']}")
        else:
            print(f"Error: {response.json()}")
    
    return intent_ids

def test_list_intents():
    """Test listing intents"""
    print("\n=== Testing List Intents ===")
    response = requests.get(f"{BASE_URL}/api/v1/intents")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Total intents: {result['count']}")
        for intent in result['intents']:
            print(f"  - {intent['id']}: {intent['description']}")

def test_get_intent(intent_id):
    """Test getting specific intent"""
    print(f"\n=== Testing Get Intent: {intent_id} ===")
    response = requests.get(f"{BASE_URL}/api/v1/intents/{intent_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        intent = response.json()['intent']
        print(f"Description: {intent['description']}")
        print(f"Type: {intent['type']}")
        print(f"Status: {intent['status']}")
        print(f"Policies: {len(intent['policies'])}")

def test_list_policies():
    """Test listing all policies"""
    print("\n=== Testing List Policies ===")
    response = requests.get(f"{BASE_URL}/api/v1/policies")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Total policies: {result['count']}")
        for policy in result['policies']:
            print(f"  - {policy['policy_id']}: {policy['policy_type']} -> {policy['target']}")

def main():
    """Run all tests"""
    print("=" * 60)
    print("Imperium System Test")
    print("=" * 60)
    
    try:
        # Test health
        if not test_health():
            print("\n❌ Health check failed! Is the API running?")
            print("Start it with: python src/intent_manager/api.py")
            return
        
        print("\n✅ API is healthy!")
        
        # Submit test intents
        intent_ids = test_submit_intent()
        
        if intent_ids:
            print(f"\n✅ Successfully created {len(intent_ids)} intents")
            
            # List all intents
            test_list_intents()
            
            # Get first intent details
            if intent_ids:
                test_get_intent(intent_ids[0])
            
            # List all policies
            test_list_policies()
            
            print("\n" + "=" * 60)
            print("✅ All tests completed successfully!")
            print("=" * 60)
        else:
            print("\n❌ No intents were created")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to API!")
        print("Make sure the Intent Manager is running:")
        print("  python src/intent_manager/api.py")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == '__main__':
    main()
