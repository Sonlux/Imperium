"""
Rate limiting module for Imperium Intent-Based Networking system.

Provides configurable rate limiting to protect API endpoints from abuse.
"""

from flask import request, jsonify
from functools import wraps
from collections import defaultdict
from datetime import datetime, timedelta
import threading


class RateLimiter:
    """In-memory rate limiter with configurable limits per endpoint."""
    
    def __init__(self):
        """Initialize rate limiter."""
        self.requests = defaultdict(list)  # {client_id: [timestamps]}
        self.lock = threading.Lock()
        
        # Default rate limits (requests per time window)
        self.limits = {
            'default': {'requests': 1000, 'window': 3600},  # 1000 requests per hour
            'auth': {'requests': 100, 'window': 3600},      # 100 requests per hour for auth
            'intents': {'requests': 500, 'window': 3600},   # 500 intents per hour
            'high': {'requests': 2000, 'window': 3600}      # 2000 requests per hour for privileged users
        }
    
    def get_client_id(self):
        """Get client identifier from request.
        
        Returns:
            Client identifier (IP address or username)
        """
        # Try to get username from request context (if authenticated)
        if hasattr(request, 'current_user'):
            return f"user:{request.current_user.get('username')}"
        
        # Fall back to IP address
        return f"ip:{request.remote_addr}"
    
    def is_rate_limited(self, client_id, limit_type='default'):
        """Check if client has exceeded rate limit.
        
        Args:
            client_id: Client identifier
            limit_type: Type of rate limit to apply
            
        Returns:
            Tuple of (is_limited: bool, remaining: int, reset_time: datetime)
        """
        with self.lock:
            now = datetime.utcnow()
            limit_config = self.limits.get(limit_type, self.limits['default'])
            max_requests = limit_config['requests']
            window_seconds = limit_config['window']
            window_start = now - timedelta(seconds=window_seconds)
            
            # Get request history for this client
            request_times = self.requests[client_id]
            
            # Remove old requests outside the time window
            request_times = [t for t in request_times if t > window_start]
            self.requests[client_id] = request_times
            
            # Check if limit exceeded
            is_limited = len(request_times) >= max_requests
            remaining = max(0, max_requests - len(request_times))
            
            # Calculate reset time (when oldest request in window expires)
            if request_times:
                reset_time = request_times[0] + timedelta(seconds=window_seconds)
            else:
                reset_time = now + timedelta(seconds=window_seconds)
            
            # Add current request if not limited
            if not is_limited:
                request_times.append(now)
            
            return is_limited, remaining, reset_time
    
    def limit(self, limit_type='default'):
        """Decorator to apply rate limiting to endpoints.
        
        Args:
            limit_type: Type of rate limit to apply
            
        Usage:
            @app.route('/api/endpoint')
            @rate_limiter.limit('intents')
            def endpoint():
                return "Success"
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                client_id = self.get_client_id()
                is_limited, remaining, reset_time = self.is_rate_limited(client_id, limit_type)
                
                if is_limited:
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'message': f'Too many requests. Try again after {reset_time.isoformat()}',
                        'retry_after': reset_time.isoformat()
                    }), 429
                
                # Add rate limit headers to response
                response = f(*args, **kwargs)
                if hasattr(response, 'headers'):
                    response.headers['X-RateLimit-Limit'] = str(self.limits[limit_type]['requests'])
                    response.headers['X-RateLimit-Remaining'] = str(remaining)
                    response.headers['X-RateLimit-Reset'] = reset_time.isoformat()
                
                return response
            
            return decorated_function
        
        return decorator
    
    def configure_limits(self, limits):
        """Update rate limit configuration.
        
        Args:
            limits: Dictionary of limit configurations
                    e.g., {'default': {'requests': 100, 'window': 3600}}
        """
        with self.lock:
            self.limits.update(limits)
    
    def reset_client(self, client_id):
        """Reset rate limit for specific client.
        
        Args:
            client_id: Client identifier
        """
        with self.lock:
            if client_id in self.requests:
                del self.requests[client_id]
    
    def get_stats(self):
        """Get rate limiting statistics.
        
        Returns:
            Dictionary with current rate limit stats
        """
        with self.lock:
            now = datetime.utcnow()
            stats = {
                'total_clients': len(self.requests),
                'active_clients': 0,
                'clients': []
            }
            
            for client_id, request_times in self.requests.items():
                # Count clients with requests in last hour
                recent_requests = [t for t in request_times if t > now - timedelta(hours=1)]
                if recent_requests:
                    stats['active_clients'] += 1
                    stats['clients'].append({
                        'client_id': client_id,
                        'recent_requests': len(recent_requests),
                        'total_requests': len(request_times)
                    })
            
            return stats


class IPWhitelist:
    """IP whitelist manager for bypassing rate limits."""
    
    def __init__(self):
        """Initialize IP whitelist."""
        self.whitelist = set()
        self.lock = threading.Lock()
    
    def add(self, ip_address):
        """Add IP to whitelist.
        
        Args:
            ip_address: IP address to whitelist
        """
        with self.lock:
            self.whitelist.add(ip_address)
    
    def remove(self, ip_address):
        """Remove IP from whitelist.
        
        Args:
            ip_address: IP address to remove
        """
        with self.lock:
            self.whitelist.discard(ip_address)
    
    def is_whitelisted(self, ip_address):
        """Check if IP is whitelisted.
        
        Args:
            ip_address: IP address to check
            
        Returns:
            Boolean indicating if IP is whitelisted
        """
        with self.lock:
            return ip_address in self.whitelist
    
    def check(self, f):
        """Decorator to bypass rate limit for whitelisted IPs.
        
        Usage:
            @app.route('/api/endpoint')
            @ip_whitelist.check
            @rate_limiter.limit()
            def endpoint():
                return "Success"
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if self.is_whitelisted(request.remote_addr):
                # Skip rate limiting for whitelisted IPs
                return f(*args, **kwargs)
            return f(*args, **kwargs)
        
        return decorated_function
