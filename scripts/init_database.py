"""
Database initialization script for Imperium Intent-Based Networking system.

This script:
1. Creates all database tables
2. Creates default admin user
3. Migrates existing in-memory data (if any)
"""

import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import DatabaseManager
from src.auth import AuthManager, create_default_admin


def init_database(db_path='data/imperium.db', create_admin=True):
    """Initialize database with tables and default data.
    
    Args:
        db_path: Path to SQLite database file
        create_admin: Whether to create default admin user
        
    Returns:
        Tuple of (DatabaseManager, AuthManager) instances
    """
    print("=" * 60)
    print("Imperium Database Initialization")
    print("=" * 60)
    
    # Create database manager
    print(f"\n1. Creating database: {db_path}")
    db_manager = DatabaseManager(db_path=db_path)
    print("   ✓ Database created successfully")
    print("   ✓ Tables: intents, policies, metrics_history, users")
    
    # Create auth manager
    print("\n2. Initializing authentication system")
    auth_manager = AuthManager(db_manager=db_manager)
    print("   ✓ Authentication system initialized")
    
    # Create default admin user
    if create_admin:
        print("\n3. Creating default admin user")
        success = create_default_admin(auth_manager, username='admin', password='admin')
        if success:
            print("   ✓ Admin user created")
            print("   📝 Username: admin")
            print("   📝 Password: admin")
            print("   ⚠️  IMPORTANT: Change the default password immediately!")
        else:
            print("   ⚠️  Admin user already exists or creation failed")
    
    print("\n" + "=" * 60)
    print("Database initialization complete!")
    print("=" * 60)
    
    return db_manager, auth_manager


def migrate_in_memory_data(db_manager, intent_manager=None, policy_engine=None):
    """Migrate existing in-memory data to persistent database.
    
    Args:
        db_manager: DatabaseManager instance
        intent_manager: IntentManager instance (if available)
        policy_engine: PolicyEngine instance (if available)
    """
    print("\n" + "=" * 60)
    print("Migrating In-Memory Data to Database")
    print("=" * 60)
    
    migrated_intents = 0
    migrated_policies = 0
    
    # Migrate intents
    if intent_manager and hasattr(intent_manager, 'intents'):
        print("\n1. Migrating intents...")
        for intent_id, intent_data in intent_manager.intents.items():
            try:
                db_manager.add_intent(
                    intent_id=intent_id,
                    original_intent=intent_data.get('original_intent', ''),
                    parsed_intent=intent_data.get('parsed_intent'),
                    status=intent_data.get('status', 'active')
                )
                migrated_intents += 1
            except Exception as e:
                print(f"   ✗ Failed to migrate intent {intent_id}: {e}")
        
        print(f"   ✓ Migrated {migrated_intents} intents")
    
    # Migrate policies
    if policy_engine and hasattr(policy_engine, 'policies'):
        print("\n2. Migrating policies...")
        for policy_id, policy_data in policy_engine.policies.items():
            try:
                db_manager.add_policy(
                    policy_id=policy_id,
                    intent_id=policy_data.get('intent_id', ''),
                    policy_type=policy_data.get('type', 'unknown'),
                    parameters=policy_data.get('parameters'),
                    status=policy_data.get('status', 'enforced')
                )
                migrated_policies += 1
            except Exception as e:
                print(f"   ✗ Failed to migrate policy {policy_id}: {e}")
        
        print(f"   ✓ Migrated {migrated_policies} policies")
    
    print("\n" + "=" * 60)
    print(f"Migration complete! ({migrated_intents} intents, {migrated_policies} policies)")
    print("=" * 60)


def verify_database(db_manager):
    """Verify database is working correctly.
    
    Args:
        db_manager: DatabaseManager instance
    """
    print("\n" + "=" * 60)
    print("Database Verification")
    print("=" * 60)
    
    try:
        # Test intent operations
        print("\n1. Testing intent operations...")
        test_intent = db_manager.add_intent(
            intent_id='test-intent-001',
            original_intent='Test intent for verification',
            parsed_intent={'action': 'test'},
            status='test'
        )
        retrieved = db_manager.get_intent('test-intent-001')
        assert retrieved is not None
        print("   ✓ Intent add/retrieve working")
        
        # Test policy operations
        print("\n2. Testing policy operations...")
        test_policy = db_manager.add_policy(
            policy_id='test-policy-001',
            intent_id='test-intent-001',
            policy_type='test',
            parameters={'test': True},
            status='test'
        )
        policies = db_manager.get_all_policies(limit=1)
        assert len(policies) > 0
        print("   ✓ Policy add/retrieve working")
        
        # Test metrics operations
        print("\n3. Testing metrics operations...")
        test_metric = db_manager.add_metric(
            metric_name='test_metric',
            metric_value=123.45,
            device_id='test-device',
            intent_id='test-intent-001'
        )
        metrics = db_manager.get_metrics(metric_name='test_metric')
        assert len(metrics) > 0
        print("   ✓ Metrics add/retrieve working")
        
        print("\n" + "=" * 60)
        print("✓ Database verification passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Database verification failed: {e}")
        raise


if __name__ == '__main__':
    # Initialize database
    db_manager, auth_manager = init_database()
    
    # Verify database is working
    verify_database(db_manager)
    
    print("\n✨ Ready to use!")
    print("\nNext steps:")
    print("1. Update main.py to use DatabaseManager")
    print("2. Add authentication endpoints to API")
    print("3. Protect API endpoints with @auth_manager.require_auth")
    print("4. Test the full system with authentication\n")
