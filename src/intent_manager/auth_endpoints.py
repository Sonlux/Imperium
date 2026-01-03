"""
Authentication endpoints for Imperium API.

Provides login, logout, user registration, and token validation endpoints.
"""

from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')


def init_auth_endpoints(app, auth_manager, rate_limiter):
    """Initialize authentication endpoints.
    
    Args:
        app: Flask application instance
        auth_manager: AuthManager instance
        rate_limiter: RateLimiter instance
    """
    
    @auth_bp.route('/register', methods=['POST'])
    @rate_limiter.limit('auth')
    def register():
        """Register a new user account.
        
        Request body:
            {
                "username": "john_doe",
                "password": "secure_password",
                "email": "john@example.com" (optional)
            }
        
        Returns:
            201: User created successfully
            400: Invalid request data
            409: Username already exists
        """
        data = request.get_json()
        
        # Validate input
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({
                'error': 'Missing required fields',
                'message': 'Username and password are required'
            }), 400
        
        username = data['username']
        password = data['password']
        email = data.get('email')
        
        # Check username format
        if len(username) < 3 or len(username) > 50:
            return jsonify({
                'error': 'Invalid username',
                'message': 'Username must be between 3 and 50 characters'
            }), 400
        
        # Check password strength
        if len(password) < 8:
            return jsonify({
                'error': 'Weak password',
                'message': 'Password must be at least 8 characters'
            }), 400
        
        # Check if user already exists
        existing_user = auth_manager.db_manager.get_user_by_username(username)
        if existing_user:
            return jsonify({
                'error': 'Username already exists',
                'message': f'User "{username}" is already registered'
            }), 409
        
        # Register user
        user = auth_manager.register_user(username, password, email=email, role='user')
        
        if user:
            logger.info(f"New user registered: {username}")
            return jsonify({
                'message': 'User registered successfully',
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'role': user['role']
                }
            }), 201
        else:
            return jsonify({
                'error': 'Registration failed',
                'message': 'Could not create user account'
            }), 500
    
    @auth_bp.route('/login', methods=['POST'])
    @rate_limiter.limit('auth')
    def login():
        """Authenticate user and generate JWT token.
        
        Request body:
            {
                "username": "john_doe",
                "password": "secure_password"
            }
        
        Returns:
            200: Authentication successful with JWT token
            400: Invalid request data
            401: Invalid credentials
        """
        data = request.get_json()
        
        # Validate input
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({
                'error': 'Missing credentials',
                'message': 'Username and password are required'
            }), 400
        
        username = data['username']
        password = data['password']
        
        # Authenticate user
        token = auth_manager.authenticate_user(username, password)
        
        if token:
            logger.info(f"User logged in: {username}")
            return jsonify({
                'message': 'Login successful',
                'token': token,
                'token_type': 'Bearer',
                'expires_in': auth_manager.token_expiry_hours * 3600  # seconds
            }), 200
        else:
            logger.warning(f"Failed login attempt for user: {username}")
            return jsonify({
                'error': 'Authentication failed',
                'message': 'Invalid username or password'
            }), 401
    
    @auth_bp.route('/verify', methods=['GET'])
    def verify_token():
        """Verify JWT token validity.
        
        Headers:
            Authorization: Bearer <token>
        
        Returns:
            200: Token is valid with user info
            401: Token is invalid or expired
        """
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'error': 'No token provided',
                'message': 'Authorization header is missing'
            }), 401
        
        try:
            token = auth_header.split(' ')[1]
        except IndexError:
            return jsonify({
                'error': 'Invalid authorization header',
                'message': 'Format should be: Bearer <token>'
            }), 401
        
        # Verify token
        payload = auth_manager.decode_token(token)
        
        if payload:
            return jsonify({
                'valid': True,
                'user': {
                    'username': payload['username'],
                    'role': payload['role'],
                    'expires_at': payload['exp']
                }
            }), 200
        else:
            return jsonify({
                'valid': False,
                'error': 'Invalid or expired token'
            }), 401
    
    @auth_bp.route('/profile', methods=['GET'])
    @auth_manager.require_auth
    def get_profile():
        """Get current user profile.
        
        Headers:
            Authorization: Bearer <token>
        
        Returns:
            200: User profile information
            401: Not authenticated
        """
        current_user = request.current_user
        username = current_user['username']
        
        # Get user from database
        user = auth_manager.db_manager.get_user_by_username(username)
        
        if user:
            return jsonify({
                'user': user.to_dict()
            }), 200
        else:
            return jsonify({
                'error': 'User not found'
            }), 404
    
    # Register blueprint
    app.register_blueprint(auth_bp)
    logger.info("✓ Authentication endpoints registered")
