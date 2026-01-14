"""
Authentication module for Imperium Intent-Based Networking system.

Provides JWT-based authentication for API endpoints with role-based access control.
"""

from flask import request, jsonify
from functools import wraps
from datetime import datetime, timedelta
import jwt
import bcrypt
import os
from src.database import DatabaseManager


class AuthManager:
    """Manager for authentication and authorization."""
    
    def __init__(self, secret_key=None, db_manager=None):
        """Initialize authentication manager.
        
        Args:
            secret_key: JWT secret key (defaults to env var or random)
            db_manager: DatabaseManager instance
        """
        self.secret_key = secret_key or os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
        self.db_manager = db_manager or DatabaseManager()
        self.token_expiry_hours = 24
    
    def hash_password(self, password):
        """Hash password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password, password_hash):
        """Verify password against hash.
        
        Args:
            password: Plain text password
            password_hash: Stored password hash
            
        Returns:
            Boolean indicating if password is correct
        """
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def generate_token(self, username, role='user'):
        """Generate JWT token for user.
        
        Args:
            username: Username
            role: User role (user/admin)
            
        Returns:
            JWT token string
        """
        payload = {
            'username': username,
            'role': role,
            'exp': datetime.utcnow() + timedelta(hours=self.token_expiry_hours),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def decode_token(self, token):
        """Decode and validate JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload dict or None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def register_user(self, username, password, email=None, role='user'):
        """Register new user.
        
        Args:
            username: Username
            password: Plain text password
            email: Email address (optional)
            role: User role
            
        Returns:
            User dict or None if registration failed
        """
        try:
            password_hash = self.hash_password(password)
            user = self.db_manager.add_user(username, password_hash, email, role)
            return user
        except Exception as e:
            print(f"User registration failed: {e}")
            return None
    
    def authenticate_user(self, username, password):
        """Authenticate user with username and password.
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            JWT token if successful, None otherwise
        """
        user = self.db_manager.get_user_by_username(username)
        if not user or not user.is_active:
            return None
        
        if self.verify_password(password, user.password_hash):
            self.db_manager.update_last_login(username)
            return self.generate_token(user.username, user.role)
        
        return None
    
    def require_auth(self, f):
        """Decorator to require authentication for endpoints.
        
        Usage:
            @app.route('/protected')
            @auth_manager.require_auth
            def protected_route():
                return "This is protected"
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = None
            
            # Get token from Authorization header
            auth_header = request.headers.get('Authorization')
            if auth_header:
                try:
                    token = auth_header.split(' ')[1]  # Format: "Bearer <token>"
                except IndexError:
                    return jsonify({'error': 'Invalid authorization header format'}), 401
            
            if not token:
                return jsonify({'error': 'Authentication token is missing'}), 401
            
            # Verify token
            payload = self.decode_token(token)
            if not payload:
                return jsonify({'error': 'Invalid or expired token'}), 401
            
            # Add user info to request context
            request.current_user = payload
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    def require_admin(self, f):
        """Decorator to require admin role for endpoints.
        
        Usage:
            @app.route('/admin-only')
            @auth_manager.require_admin
            def admin_route():
                return "Admin only"
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = None
            
            # Get token from Authorization header
            auth_header = request.headers.get('Authorization')
            if auth_header:
                try:
                    token = auth_header.split(' ')[1]
                except IndexError:
                    return jsonify({'error': 'Invalid authorization header format'}), 401
            
            if not token:
                return jsonify({'error': 'Authentication token is missing'}), 401
            
            # Verify token
            payload = self.decode_token(token)
            if not payload:
                return jsonify({'error': 'Invalid or expired token'}), 401
            
            # Check admin role
            if payload.get('role') != 'admin':
                return jsonify({'error': 'Admin privileges required'}), 403
            
            # Add user info to request context
            request.current_user = payload
            
            return f(*args, **kwargs)
        
        return decorated_function


def create_default_admin(auth_manager, username='admin', password='admin'):
    """Create default admin user for initial setup.
    
    Args:
        auth_manager: AuthManager instance
        username: Admin username
        password: Admin password
        
    Returns:
        Boolean indicating success
    """
    try:
        # Check if admin already exists
        existing_user = auth_manager.db_manager.get_user_by_username(username)
        if existing_user:
            print(f"User '{username}' already exists")
            return False
        
        # Create admin user
        user = auth_manager.register_user(username, password, role='admin')
        if user:
            print(f"✓ Created default admin user: {username}")
            return True
        else:
            print("✗ Failed to create admin user")
            return False
    except Exception as e:
        print(f"Error creating admin user: {e}")
        return False
