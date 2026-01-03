"""
Database models and operations for Imperium Intent-Based Networking system.

This module provides SQLAlchemy ORM models for persistent storage of:
- Intents: User-submitted high-level network intentions
- Policies: Generated network policies from intents
- Metrics History: Time-series data for feedback loop analysis
"""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import json
import os

Base = declarative_base()


class Intent(Base):
    """Model for storing user intents."""
    __tablename__ = 'intents'
    
    id = Column(String(36), primary_key=True)  # UUID
    original_intent = Column(Text, nullable=False)
    parsed_intent = Column(Text)  # JSON string
    status = Column(String(20), default='pending')  # pending, active, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    policies = relationship("Policy", back_populates="intent", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert intent to dictionary."""
        return {
            'id': self.id,
            'original_intent': self.original_intent,
            'parsed_intent': json.loads(self.parsed_intent) if self.parsed_intent else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'policies': [p.to_dict() for p in self.policies] if self.policies else []
        }


class Policy(Base):
    """Model for storing generated policies."""
    __tablename__ = 'policies'
    
    id = Column(String(36), primary_key=True)  # UUID
    intent_id = Column(String(36), ForeignKey('intents.id'), nullable=False)
    type = Column(String(50), nullable=False)  # tc_commands, mqtt_configs, routing_rules, etc.
    parameters = Column(Text)  # JSON string
    status = Column(String(20), default='pending')  # pending, enforced, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    enforced_at = Column(DateTime, nullable=True)
    
    # Relationship
    intent = relationship("Intent", back_populates="policies")
    
    def to_dict(self):
        """Convert policy to dictionary."""
        return {
            'id': self.id,
            'intent_id': self.intent_id,
            'type': self.type,
            'parameters': json.loads(self.parameters) if self.parameters else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'enforced_at': self.enforced_at.isoformat() if self.enforced_at else None
        }


class MetricsHistory(Base):
    """Model for storing historical metrics data."""
    __tablename__ = 'metrics_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    device_id = Column(String(50), nullable=True, index=True)
    intent_id = Column(String(36), nullable=True, index=True)
    meta_data = Column(Text, nullable=True)  # Renamed from 'metadata' - JSON string for additional context
    
    def to_dict(self):
        """Convert metrics to dictionary."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'device_id': self.device_id,
            'intent_id': self.intent_id,
            'meta_data': json.loads(self.meta_data) if self.meta_data else None
        }


class User(Base):
    """Model for storing user accounts (for API authentication)."""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)  # Hashed password
    email = Column(String(120), nullable=True)
    role = Column(String(20), default='user')  # user, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    def to_dict(self):
        """Convert user to dictionary (excluding password)."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


class DatabaseManager:
    """Manager class for database operations."""
    
    def __init__(self, db_path='data/imperium.db'):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        # Create data directory if it doesn't exist
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def get_session(self):
        """Get a new database session."""
        return self.Session()
    
    def add_intent(self, intent_id, original_intent, parsed_intent, status='pending'):
        """Add new intent to database."""
        session = self.get_session()
        try:
            intent = Intent(
                id=intent_id,
                original_intent=original_intent,
                parsed_intent=json.dumps(parsed_intent) if parsed_intent else None,
                status=status
            )
            session.add(intent)
            session.commit()
            return intent.to_dict()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def add_policy(self, policy_id, intent_id, policy_type, parameters, status='pending'):
        """Add new policy to database."""
        session = self.get_session()
        try:
            policy = Policy(
                id=policy_id,
                intent_id=intent_id,
                type=policy_type,
                parameters=json.dumps(parameters) if parameters else None,
                status=status
            )
            session.add(policy)
            session.commit()
            return policy.to_dict()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def update_intent_status(self, intent_id, status):
        """Update intent status."""
        session = self.get_session()
        try:
            intent = session.query(Intent).filter_by(id=intent_id).first()
            if intent:
                intent.status = status
                intent.updated_at = datetime.utcnow()
                session.commit()
                return intent.to_dict()
            return None
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def update_policy_status(self, policy_id, status):
        """Update policy status."""
        session = self.get_session()
        try:
            policy = session.query(Policy).filter_by(id=policy_id).first()
            if policy:
                policy.status = status
                if status == 'enforced':
                    policy.enforced_at = datetime.utcnow()
                session.commit()
                return policy.to_dict()
            return None
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_intent(self, intent_id):
        """Get intent by ID."""
        session = self.get_session()
        try:
            intent = session.query(Intent).filter_by(id=intent_id).first()
            return intent.to_dict() if intent else None
        finally:
            session.close()
    
    def get_all_intents(self, limit=100):
        """Get all intents."""
        session = self.get_session()
        try:
            intents = session.query(Intent).order_by(Intent.created_at.desc()).limit(limit).all()
            return [intent.to_dict() for intent in intents]
        finally:
            session.close()
    
    def get_all_policies(self, limit=100):
        """Get all policies."""
        session = self.get_session()
        try:
            policies = session.query(Policy).order_by(Policy.created_at.desc()).limit(limit).all()
            return [policy.to_dict() for policy in policies]
        finally:
            session.close()
    
    def add_metric(self, metric_name, metric_value, device_id=None, intent_id=None, meta_data=None):
        """Add metrics data."""
        session = self.get_session()
        try:
            metric = MetricsHistory(
                metric_name=metric_name,
                metric_value=metric_value,
                device_id=device_id,
                intent_id=intent_id,
                meta_data=json.dumps(meta_data) if meta_data else None
            )
            session.add(metric)
            session.commit()
            return metric.to_dict()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_metrics(self, metric_name=None, device_id=None, start_time=None, end_time=None, limit=1000):
        """Query metrics with filters."""
        session = self.get_session()
        try:
            query = session.query(MetricsHistory)
            
            if metric_name:
                query = query.filter_by(metric_name=metric_name)
            if device_id:
                query = query.filter_by(device_id=device_id)
            if start_time:
                query = query.filter(MetricsHistory.timestamp >= start_time)
            if end_time:
                query = query.filter(MetricsHistory.timestamp <= end_time)
            
            metrics = query.order_by(MetricsHistory.timestamp.desc()).limit(limit).all()
            return [metric.to_dict() for metric in metrics]
        finally:
            session.close()
    
    def add_user(self, username, password_hash, email=None, role='user'):
        """Add new user."""
        session = self.get_session()
        try:
            user = User(
                username=username,
                password_hash=password_hash,
                email=email,
                role=role
            )
            session.add(user)
            session.commit()
            return user.to_dict()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_user_by_username(self, username):
        """Get user by username."""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(username=username).first()
            return user
        finally:
            session.close()
    
    def update_last_login(self, username):
        """Update user's last login time."""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(username=username).first()
            if user:
                user.last_login = datetime.utcnow()
                session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
