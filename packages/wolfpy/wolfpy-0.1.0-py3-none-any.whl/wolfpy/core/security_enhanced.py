"""
Enhanced Security Module for WolfPy Framework.

This module provides comprehensive security features including:
- Advanced input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF protection enhancements
- Rate limiting improvements
- Security headers management
- Content Security Policy (CSP)
- Authentication security
"""

import re
import html
import hashlib
import secrets
import time
import ipaddress
from typing import Dict, List, Any, Optional, Union, Pattern
from dataclasses import dataclass, field
from collections import defaultdict, deque
import threading
import json
import base64
from urllib.parse import quote, unquote


@dataclass
class SecurityConfig:
    """Security configuration settings."""
    # Input validation
    max_input_length: int = 10000
    allowed_file_types: List[str] = field(default_factory=lambda: [
        'jpg', 'jpeg', 'png', 'gif', 'pdf', 'txt', 'doc', 'docx'
    ])
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    
    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # 1 hour
    rate_limit_burst: int = 10
    
    # CSRF protection
    csrf_token_length: int = 32
    csrf_token_ttl: int = 3600  # 1 hour
    
    # Password security
    min_password_length: int = 8
    require_password_complexity: bool = True
    password_hash_rounds: int = 12
    
    # Session security
    session_timeout: int = 1800  # 30 minutes
    session_regenerate_interval: int = 300  # 5 minutes
    
    # Content Security Policy
    csp_enabled: bool = True
    csp_directives: Dict[str, str] = field(default_factory=lambda: {
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline'",
        'style-src': "'self' 'unsafe-inline'",
        'img-src': "'self' data: https:",
        'font-src': "'self'",
        'connect-src': "'self'",
        'frame-ancestors': "'none'"
    })


class InputValidator:
    """Advanced input validation and sanitization."""
    
    # Common regex patterns
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    URL_PATTERN = re.compile(r'^https?://[^\s/$.?#].[^\s]*$', re.IGNORECASE)
    PHONE_PATTERN = re.compile(r'^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$')
    SQL_INJECTION_PATTERNS = [
        re.compile(r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)", re.IGNORECASE),
        re.compile(r"(\b(OR|AND)\s+\d+\s*=\s*\d+)", re.IGNORECASE),
        re.compile(r"('|(\\')|(;)|(\\;)|(\-\-)|(/\*)|(\*/)|(\bxp_))", re.IGNORECASE),
        re.compile(r"(\b(script|javascript|vbscript|onload|onerror|onclick)\b)", re.IGNORECASE)
    ]
    XSS_PATTERNS = [
        re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
        re.compile(r'javascript:', re.IGNORECASE),
        re.compile(r'on\w+\s*=', re.IGNORECASE),
        re.compile(r'<iframe[^>]*>.*?</iframe>', re.IGNORECASE | re.DOTALL),
        re.compile(r'<object[^>]*>.*?</object>', re.IGNORECASE | re.DOTALL),
        re.compile(r'<embed[^>]*>', re.IGNORECASE),
        re.compile(r'<link[^>]*>', re.IGNORECASE)
    ]
    
    def __init__(self, config: SecurityConfig = None):
        """Initialize input validator."""
        self.config = config or SecurityConfig()
    
    def validate_email(self, email: str) -> bool:
        """Validate email address format."""
        if not email or len(email) > 254:
            return False
        return bool(self.EMAIL_PATTERN.match(email))
    
    def validate_url(self, url: str) -> bool:
        """Validate URL format."""
        if not url or len(url) > 2048:
            return False
        return bool(self.URL_PATTERN.match(url))
    
    def validate_phone(self, phone: str) -> bool:
        """Validate phone number format."""
        if not phone:
            return False
        return bool(self.PHONE_PATTERN.match(phone))
    
    def sanitize_html(self, text: str) -> str:
        """Sanitize HTML content to prevent XSS."""
        if not text:
            return ""
        
        # HTML escape
        sanitized = html.escape(text)
        
        # Remove potentially dangerous patterns
        for pattern in self.XSS_PATTERNS:
            sanitized = pattern.sub('', sanitized)
        
        return sanitized
    
    def detect_sql_injection(self, text: str) -> bool:
        """Detect potential SQL injection attempts."""
        if not text:
            return False
        
        text_lower = text.lower()
        
        for pattern in self.SQL_INJECTION_PATTERNS:
            if pattern.search(text):
                return True
        
        return False
    
    def validate_input_length(self, text: str, max_length: int = None) -> bool:
        """Validate input length."""
        if not text:
            return True
        
        max_len = max_length or self.config.max_input_length
        return len(text) <= max_len
    
    def validate_file_upload(self, filename: str, file_size: int, file_content: bytes = None) -> Dict[str, Any]:
        """Validate file upload."""
        result = {
            'valid': True,
            'errors': []
        }
        
        # Check filename
        if not filename:
            result['valid'] = False
            result['errors'].append("Filename is required")
            return result
        
        # Check file extension
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        if file_ext not in self.config.allowed_file_types:
            result['valid'] = False
            result['errors'].append(f"File type '{file_ext}' not allowed")
        
        # Check file size
        if file_size > self.config.max_file_size:
            result['valid'] = False
            result['errors'].append(f"File size exceeds limit ({self.config.max_file_size} bytes)")
        
        # Check for malicious content (basic)
        if file_content:
            if self._contains_malicious_content(file_content):
                result['valid'] = False
                result['errors'].append("File contains potentially malicious content")
        
        return result
    
    def _contains_malicious_content(self, content: bytes) -> bool:
        """Check for malicious content in file."""
        try:
            # Convert to string for pattern matching
            text_content = content.decode('utf-8', errors='ignore')
            
            # Check for script tags and other dangerous patterns
            dangerous_patterns = [
                b'<script',
                b'javascript:',
                b'vbscript:',
                b'data:text/html',
                b'<?php',
                b'<%',
                b'#!/bin/sh',
                b'#!/bin/bash'
            ]
            
            content_lower = content.lower()
            for pattern in dangerous_patterns:
                if pattern in content_lower:
                    return True
            
            return False
        except:
            return False
    
    def validate_password(self, password: str) -> Dict[str, Any]:
        """Validate password strength."""
        result = {
            'valid': True,
            'score': 0,
            'errors': []
        }
        
        if not password:
            result['valid'] = False
            result['errors'].append("Password is required")
            return result
        
        # Length check
        if len(password) < self.config.min_password_length:
            result['valid'] = False
            result['errors'].append(f"Password must be at least {self.config.min_password_length} characters")
        else:
            result['score'] += 1
        
        if not self.config.require_password_complexity:
            return result
        
        # Complexity checks
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        
        complexity_score = sum([has_upper, has_lower, has_digit, has_special])
        result['score'] += complexity_score
        
        if complexity_score < 3:
            result['valid'] = False
            result['errors'].append("Password must contain uppercase, lowercase, numbers, and special characters")
        
        # Common password check
        if self._is_common_password(password):
            result['valid'] = False
            result['errors'].append("Password is too common")
        
        return result
    
    def _is_common_password(self, password: str) -> bool:
        """Check if password is in common passwords list."""
        common_passwords = {
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey'
        }
        return password.lower() in common_passwords


class EnhancedRateLimiter:
    """Enhanced rate limiting with multiple strategies."""
    
    def __init__(self, config: SecurityConfig = None):
        """Initialize rate limiter."""
        self.config = config or SecurityConfig()
        self._requests = defaultdict(deque)
        self._blocked_ips = {}
        self._lock = threading.RLock()
    
    def is_allowed(self, identifier: str, endpoint: str = None) -> Dict[str, Any]:
        """Check if request is allowed."""
        current_time = time.time()
        
        with self._lock:
            # Check if IP is blocked
            if identifier in self._blocked_ips:
                if current_time < self._blocked_ips[identifier]:
                    return {
                        'allowed': False,
                        'reason': 'IP temporarily blocked',
                        'retry_after': self._blocked_ips[identifier] - current_time
                    }
                else:
                    del self._blocked_ips[identifier]
            
            # Get request history for this identifier
            key = f"{identifier}:{endpoint}" if endpoint else identifier
            requests = self._requests[key]
            
            # Remove old requests outside the window
            window_start = current_time - self.config.rate_limit_window
            while requests and requests[0] < window_start:
                requests.popleft()
            
            # Check rate limit
            if len(requests) >= self.config.rate_limit_requests:
                # Block IP for burst protection
                if len(requests) >= self.config.rate_limit_requests + self.config.rate_limit_burst:
                    self._blocked_ips[identifier] = current_time + 300  # 5 minute block
                
                return {
                    'allowed': False,
                    'reason': 'Rate limit exceeded',
                    'requests_made': len(requests),
                    'limit': self.config.rate_limit_requests,
                    'window': self.config.rate_limit_window,
                    'retry_after': requests[0] + self.config.rate_limit_window - current_time
                }
            
            # Add current request
            requests.append(current_time)
            
            return {
                'allowed': True,
                'requests_made': len(requests),
                'limit': self.config.rate_limit_requests,
                'remaining': self.config.rate_limit_requests - len(requests)
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics."""
        with self._lock:
            return {
                'active_limiters': len(self._requests),
                'blocked_ips': len(self._blocked_ips),
                'total_requests': sum(len(requests) for requests in self._requests.values())
            }


class ContentSecurityPolicy:
    """Content Security Policy management."""
    
    def __init__(self, config: SecurityConfig = None):
        """Initialize CSP manager."""
        self.config = config or SecurityConfig()
    
    def generate_csp_header(self, additional_directives: Dict[str, str] = None) -> str:
        """Generate CSP header value."""
        if not self.config.csp_enabled:
            return ""
        
        directives = self.config.csp_directives.copy()
        if additional_directives:
            directives.update(additional_directives)
        
        csp_parts = []
        for directive, value in directives.items():
            csp_parts.append(f"{directive} {value}")
        
        return "; ".join(csp_parts)
    
    def validate_csp_violation(self, violation_report: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and process CSP violation report."""
        return {
            'valid': True,
            'blocked_uri': violation_report.get('blocked-uri', ''),
            'violated_directive': violation_report.get('violated-directive', ''),
            'source_file': violation_report.get('source-file', ''),
            'line_number': violation_report.get('line-number', 0),
            'timestamp': time.time()
        }


class SecurityHeadersManager:
    """Manage security headers for responses."""
    
    DEFAULT_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
    }
    
    def __init__(self, custom_headers: Dict[str, str] = None):
        """Initialize security headers manager."""
        self.headers = self.DEFAULT_HEADERS.copy()
        if custom_headers:
            self.headers.update(custom_headers)
    
    def get_security_headers(self, csp_header: str = None) -> Dict[str, str]:
        """Get all security headers."""
        headers = self.headers.copy()
        
        if csp_header:
            headers['Content-Security-Policy'] = csp_header
        
        return headers
    
    def add_header(self, name: str, value: str):
        """Add or update a security header."""
        self.headers[name] = value
    
    def remove_header(self, name: str):
        """Remove a security header."""
        self.headers.pop(name, None)


# Global instances
security_config = SecurityConfig()
input_validator = InputValidator(security_config)
rate_limiter = EnhancedRateLimiter(security_config)
csp_manager = ContentSecurityPolicy(security_config)
security_headers = SecurityHeadersManager()
