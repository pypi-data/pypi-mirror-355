"""
WolfPy Security Module.

This module provides security middleware and utilities for WolfPy applications
including CSRF protection, rate limiting, CORS, and security headers.
"""

import time
import hashlib
import secrets
import re
from typing import Dict, List, Optional, Set, Callable, Any
from collections import defaultdict, deque
from datetime import datetime, timedelta
from .middleware import BaseMiddleware
from .request import Request
from .response import Response


class CSRFProtection(BaseMiddleware):
    """CSRF protection middleware."""
    
    def __init__(self, secret_key: str, token_name: str = 'csrf_token',
                 header_name: str = 'X-CSRF-Token', cookie_name: str = 'csrf_token',
                 exempt_methods: Set[str] = None, **kwargs):
        """
        Initialize CSRF protection.
        
        Args:
            secret_key: Secret key for token generation
            token_name: Form field name for CSRF token
            header_name: HTTP header name for CSRF token
            cookie_name: Cookie name for CSRF token
            exempt_methods: HTTP methods exempt from CSRF protection
        """
        super().__init__(**kwargs)
        self.secret_key = secret_key
        self.token_name = token_name
        self.header_name = header_name
        self.cookie_name = cookie_name
        self.exempt_methods = exempt_methods or {'GET', 'HEAD', 'OPTIONS', 'TRACE'}
    
    def generate_token(self, session_id: str = None) -> str:
        """Generate CSRF token."""
        if not session_id:
            session_id = secrets.token_hex(16)
        
        timestamp = str(int(time.time()))
        data = f"{session_id}:{timestamp}:{self.secret_key}"
        token = hashlib.sha256(data.encode()).hexdigest()
        return f"{session_id}:{timestamp}:{token}"
    
    def validate_token(self, token: str, max_age: int = 3600) -> bool:
        """Validate CSRF token."""
        try:
            parts = token.split(':')
            if len(parts) != 3:
                return False
            
            session_id, timestamp, token_hash = parts
            
            # Check age
            if int(time.time()) - int(timestamp) > max_age:
                return False
            
            # Verify token
            expected_data = f"{session_id}:{timestamp}:{self.secret_key}"
            expected_hash = hashlib.sha256(expected_data.encode()).hexdigest()
            
            return secrets.compare_digest(token_hash, expected_hash)
        except (ValueError, TypeError):
            return False
    
    def process_request(self, request: Request) -> Optional[Request]:
        """Process request for CSRF protection."""
        if request.method in self.exempt_methods:
            return None
        
        # Get token from form, header, or cookie
        token = None
        if hasattr(request, 'form') and self.token_name in request.form:
            token = request.get_form(self.token_name)
        elif self.header_name in request.headers:
            token = request.headers[self.header_name]
        elif hasattr(request, 'cookies') and self.cookie_name in request.cookies:
            token = request.cookies[self.cookie_name]
        
        if not token or not self.validate_token(token):
            # Return 403 Forbidden response
            from .response import Response
            response = Response('CSRF token missing or invalid', status=403)
            raise Exception("CSRF validation failed")
        
        return None


class RateLimiter(BaseMiddleware):
    """Rate limiting middleware with multiple strategies."""
    
    def __init__(self, requests_per_minute: int = 60, requests_per_hour: int = 1000,
                 strategy: str = 'sliding_window', key_func: Callable = None,
                 storage_backend: str = 'memory', **kwargs):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Requests allowed per minute
            requests_per_hour: Requests allowed per hour
            strategy: Rate limiting strategy ('sliding_window', 'token_bucket', 'fixed_window')
            key_func: Function to generate rate limit key from request
            storage_backend: Storage backend ('memory', 'redis')
        """
        super().__init__(**kwargs)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.strategy = strategy
        self.key_func = key_func or self._default_key_func
        self.storage_backend = storage_backend
        
        # Memory storage
        self._request_counts = defaultdict(lambda: {'minute': deque(), 'hour': deque()})
        self._token_buckets = defaultdict(lambda: {'tokens': requests_per_minute, 'last_refill': time.time()})
    
    def _default_key_func(self, request: Request) -> str:
        """Default key function using client IP."""
        return request.environ.get('REMOTE_ADDR', 'unknown')
    
    def _sliding_window_check(self, key: str) -> bool:
        """Check rate limit using sliding window strategy."""
        now = time.time()
        minute_ago = now - 60
        hour_ago = now - 3600
        
        counts = self._request_counts[key]
        
        # Clean old entries
        while counts['minute'] and counts['minute'][0] < minute_ago:
            counts['minute'].popleft()
        while counts['hour'] and counts['hour'][0] < hour_ago:
            counts['hour'].popleft()
        
        # Check limits
        if len(counts['minute']) >= self.requests_per_minute:
            return False
        if len(counts['hour']) >= self.requests_per_hour:
            return False
        
        # Add current request
        counts['minute'].append(now)
        counts['hour'].append(now)
        
        return True
    
    def _token_bucket_check(self, key: str) -> bool:
        """Check rate limit using token bucket strategy."""
        now = time.time()
        bucket = self._token_buckets[key]
        
        # Refill tokens
        time_passed = now - bucket['last_refill']
        tokens_to_add = time_passed * (self.requests_per_minute / 60.0)
        bucket['tokens'] = min(self.requests_per_minute, bucket['tokens'] + tokens_to_add)
        bucket['last_refill'] = now
        
        # Check if token available
        if bucket['tokens'] >= 1:
            bucket['tokens'] -= 1
            return True
        
        return False
    
    def process_request(self, request: Request) -> Optional[Request]:
        """Process request for rate limiting."""
        key = self.key_func(request)
        
        if self.strategy == 'sliding_window':
            allowed = self._sliding_window_check(key)
        elif self.strategy == 'token_bucket':
            allowed = self._token_bucket_check(key)
        else:
            allowed = True  # Default to allow
        
        if not allowed:
            from .response import Response
            response = Response('Rate limit exceeded', status=429)
            response.headers['Retry-After'] = '60'
            raise Exception("Rate limit exceeded")
        
        return None


class CORSMiddleware(BaseMiddleware):
    """CORS (Cross-Origin Resource Sharing) middleware."""
    
    def __init__(self, allowed_origins: List[str] = None, allowed_methods: List[str] = None,
                 allowed_headers: List[str] = None, exposed_headers: List[str] = None,
                 allow_credentials: bool = False, max_age: int = 86400, **kwargs):
        """
        Initialize CORS middleware.
        
        Args:
            allowed_origins: List of allowed origins or ['*'] for all
            allowed_methods: List of allowed HTTP methods
            allowed_headers: List of allowed headers
            exposed_headers: List of headers to expose to client
            allow_credentials: Whether to allow credentials
            max_age: Preflight cache max age in seconds
        """
        super().__init__(**kwargs)
        self.allowed_origins = allowed_origins or ['*']
        self.allowed_methods = allowed_methods or ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
        self.allowed_headers = allowed_headers or ['Content-Type', 'Authorization']
        self.exposed_headers = exposed_headers or []
        self.allow_credentials = allow_credentials
        self.max_age = max_age
    
    def _is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is allowed."""
        if '*' in self.allowed_origins:
            return True
        return origin in self.allowed_origins
    
    def process_request(self, request: Request) -> Optional[Request]:
        """Handle CORS preflight requests."""
        if request.method == 'OPTIONS':
            origin = request.headers.get('Origin', '')
            
            if self._is_origin_allowed(origin):
                from .response import Response
                response = Response('', status=200)
                
                response.headers['Access-Control-Allow-Origin'] = origin if origin else '*'
                response.headers['Access-Control-Allow-Methods'] = ', '.join(self.allowed_methods)
                response.headers['Access-Control-Allow-Headers'] = ', '.join(self.allowed_headers)
                response.headers['Access-Control-Max-Age'] = str(self.max_age)
                
                if self.allow_credentials:
                    response.headers['Access-Control-Allow-Credentials'] = 'true'
                
                # Return response to short-circuit request processing
                request._cors_preflight_response = response
        
        return None
    
    def process_response(self, request: Request, response: Response) -> Optional[Response]:
        """Add CORS headers to response."""
        # Check for preflight response
        if hasattr(request, '_cors_preflight_response'):
            return request._cors_preflight_response
        
        origin = request.headers.get('Origin', '')
        
        if self._is_origin_allowed(origin):
            response.headers['Access-Control-Allow-Origin'] = origin if origin else '*'
            
            if self.exposed_headers:
                response.headers['Access-Control-Expose-Headers'] = ', '.join(self.exposed_headers)
            
            if self.allow_credentials:
                response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        return None


class SecurityHeadersMiddleware(BaseMiddleware):
    """Security headers middleware."""
    
    def __init__(self, **kwargs):
        """Initialize security headers middleware."""
        super().__init__(**kwargs)
        self.default_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Content-Security-Policy': "default-src 'self'",
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
        }
    
    def process_response(self, request: Request, response: Response) -> Optional[Response]:
        """Add security headers to response."""
        for header, value in self.default_headers.items():
            if header not in response.headers:
                response.headers[header] = value
        
        return None


class IPWhitelistMiddleware(BaseMiddleware):
    """IP whitelist/blacklist middleware."""
    
    def __init__(self, whitelist: List[str] = None, blacklist: List[str] = None, **kwargs):
        """
        Initialize IP filtering middleware.
        
        Args:
            whitelist: List of allowed IP addresses/ranges
            blacklist: List of blocked IP addresses/ranges
        """
        super().__init__(**kwargs)
        self.whitelist = whitelist or []
        self.blacklist = blacklist or []
    
    def _ip_in_range(self, ip: str, ip_range: str) -> bool:
        """Check if IP is in range (supports CIDR notation)."""
        if '/' not in ip_range:
            return ip == ip_range
        
        try:
            import ipaddress
            return ipaddress.ip_address(ip) in ipaddress.ip_network(ip_range)
        except (ValueError, ImportError):
            return ip == ip_range.split('/')[0]
    
    def process_request(self, request: Request) -> Optional[Request]:
        """Filter requests based on IP address."""
        client_ip = request.environ.get('REMOTE_ADDR', '')
        
        # Check blacklist first
        for blocked_ip in self.blacklist:
            if self._ip_in_range(client_ip, blocked_ip):
                from .response import Response
                response = Response('Access denied', status=403)
                raise Exception("IP address blocked")
        
        # Check whitelist if configured
        if self.whitelist:
            allowed = False
            for allowed_ip in self.whitelist:
                if self._ip_in_range(client_ip, allowed_ip):
                    allowed = True
                    break
            
            if not allowed:
                from .response import Response
                response = Response('Access denied', status=403)
                raise Exception("IP address not whitelisted")
        
        return None
