"""
Enhanced Middleware System for WolfPy Framework.

This module provides advanced middleware functionality including:
- Async middleware support
- Error handling middleware
- Logging and monitoring middleware
- Request/response transformation
- Circuit breaker pattern
- Retry mechanisms
"""

import asyncio
import time
import logging
import traceback
import json
from typing import Dict, List, Any, Optional, Callable, Union, Awaitable
from dataclasses import dataclass, field
from collections import defaultdict, deque
from functools import wraps
import threading
from enum import Enum


class MiddlewareType(Enum):
    """Middleware execution types."""
    SYNC = "sync"
    ASYNC = "async"
    HYBRID = "hybrid"


@dataclass
class MiddlewareConfig:
    """Middleware configuration."""
    enabled: bool = True
    priority: int = 0
    timeout: float = 30.0
    retry_attempts: int = 0
    retry_delay: float = 1.0
    circuit_breaker_enabled: bool = False
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0


@dataclass
class MiddlewareContext:
    """Context passed through middleware chain."""
    request_id: str
    start_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)


class CircuitBreaker:
    """Circuit breaker for middleware fault tolerance."""
    
    def __init__(self, threshold: int = 5, timeout: float = 60.0):
        """
        Initialize circuit breaker.
        
        Args:
            threshold: Number of failures before opening circuit
            timeout: Time to wait before trying again (seconds)
        """
        self.threshold = threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self._lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        with self._lock:
            if self.state == "OPEN":
                if time.time() - self.last_failure_time > self.timeout:
                    self.state = "HALF_OPEN"
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            try:
                result = func(*args, **kwargs)
                
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                
                return result
                
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.threshold:
                    self.state = "OPEN"
                
                raise e


class BaseEnhancedMiddleware:
    """Enhanced base middleware class."""
    
    def __init__(self, config: MiddlewareConfig = None):
        """Initialize middleware."""
        self.config = config or MiddlewareConfig()
        self.circuit_breaker = CircuitBreaker(
            threshold=self.config.circuit_breaker_threshold,
            timeout=self.config.circuit_breaker_timeout
        ) if self.config.circuit_breaker_enabled else None
        
        # Performance tracking
        self.call_count = 0
        self.error_count = 0
        self.total_time = 0.0
        self.last_error = None
        self._lock = threading.Lock()
    
    def process_request(self, request, context: MiddlewareContext):
        """Process incoming request."""
        if not self.config.enabled:
            return request
        
        start_time = time.time()
        
        try:
            if self.circuit_breaker:
                result = self.circuit_breaker.call(self._process_request, request, context)
            else:
                result = self._process_request(request, context)
            
            self._record_success(time.time() - start_time)
            return result
            
        except Exception as e:
            self._record_error(e, time.time() - start_time)
            if self.config.retry_attempts > 0:
                return self._retry_request(request, context)
            raise
    
    def process_response(self, request, response, context: MiddlewareContext):
        """Process outgoing response."""
        if not self.config.enabled:
            return response
        
        start_time = time.time()
        
        try:
            if self.circuit_breaker:
                result = self.circuit_breaker.call(self._process_response, request, response, context)
            else:
                result = self._process_response(request, response, context)
            
            self._record_success(time.time() - start_time)
            return result
            
        except Exception as e:
            self._record_error(e, time.time() - start_time)
            raise
    
    def _process_request(self, request, context: MiddlewareContext):
        """Override this method in subclasses."""
        return request
    
    def _process_response(self, request, response, context: MiddlewareContext):
        """Override this method in subclasses."""
        return response
    
    def _retry_request(self, request, context: MiddlewareContext):
        """Retry request processing."""
        for attempt in range(self.config.retry_attempts):
            try:
                time.sleep(self.config.retry_delay * (attempt + 1))
                return self._process_request(request, context)
            except Exception as e:
                if attempt == self.config.retry_attempts - 1:
                    raise e
                continue
    
    def _record_success(self, duration: float):
        """Record successful execution."""
        with self._lock:
            self.call_count += 1
            self.total_time += duration
    
    def _record_error(self, error: Exception, duration: float):
        """Record error execution."""
        with self._lock:
            self.call_count += 1
            self.error_count += 1
            self.total_time += duration
            self.last_error = str(error)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get middleware statistics."""
        with self._lock:
            avg_time = self.total_time / self.call_count if self.call_count > 0 else 0
            error_rate = self.error_count / self.call_count if self.call_count > 0 else 0
            
            return {
                'name': self.__class__.__name__,
                'enabled': self.config.enabled,
                'call_count': self.call_count,
                'error_count': self.error_count,
                'error_rate': round(error_rate * 100, 2),
                'avg_execution_time': round(avg_time, 4),
                'total_time': round(self.total_time, 4),
                'last_error': self.last_error,
                'circuit_breaker_state': self.circuit_breaker.state if self.circuit_breaker else None
            }


class RequestLoggingMiddleware(BaseEnhancedMiddleware):
    """Enhanced request logging middleware."""
    
    def __init__(self, logger: logging.Logger = None, config: MiddlewareConfig = None):
        """Initialize logging middleware."""
        super().__init__(config)
        self.logger = logger or logging.getLogger(__name__)
        self.sensitive_headers = {'authorization', 'cookie', 'x-api-key'}
        self.log_body = False
        self.max_body_length = 1000
    
    def _process_request(self, request, context: MiddlewareContext):
        """Log incoming request."""
        # Sanitize headers
        headers = {}
        for key, value in request.headers.items():
            if key.lower() in self.sensitive_headers:
                headers[key] = '[REDACTED]'
            else:
                headers[key] = value
        
        log_data = {
            'request_id': context.request_id,
            'method': request.method,
            'path': request.path,
            'query_string': request.query_string,
            'headers': headers,
            'remote_addr': getattr(request, 'remote_addr', 'unknown'),
            'user_agent': request.headers.get('User-Agent', 'unknown'),
            'timestamp': time.time()
        }
        
        if self.log_body and hasattr(request, 'data') and request.data:
            body = request.data[:self.max_body_length]
            if len(request.data) > self.max_body_length:
                body += b'...[truncated]'
            log_data['body'] = body.decode('utf-8', errors='ignore')
        
        self.logger.info(f"Request: {json.dumps(log_data)}")
        context.metadata['request_logged'] = True
        
        return request
    
    def _process_response(self, request, response, context: MiddlewareContext):
        """Log outgoing response."""
        duration = time.time() - context.start_time
        
        log_data = {
            'request_id': context.request_id,
            'status_code': getattr(response, 'status', 'unknown'),
            'content_length': len(getattr(response, 'body', '')),
            'duration_ms': round(duration * 1000, 2),
            'timestamp': time.time()
        }
        
        # Log level based on status code
        if hasattr(response, 'status'):
            if response.status >= 500:
                self.logger.error(f"Response: {json.dumps(log_data)}")
            elif response.status >= 400:
                self.logger.warning(f"Response: {json.dumps(log_data)}")
            else:
                self.logger.info(f"Response: {json.dumps(log_data)}")
        else:
            self.logger.info(f"Response: {json.dumps(log_data)}")
        
        return response


class ErrorHandlingMiddleware(BaseEnhancedMiddleware):
    """Enhanced error handling middleware."""
    
    def __init__(self, config: MiddlewareConfig = None):
        """Initialize error handling middleware."""
        super().__init__(config)
        self.error_handlers = {}
        self.default_error_response = {
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }
    
    def register_error_handler(self, exception_type: type, handler: Callable):
        """Register custom error handler."""
        self.error_handlers[exception_type] = handler
    
    def _process_request(self, request, context: MiddlewareContext):
        """Process request with error handling."""
        try:
            return request
        except Exception as e:
            context.errors.append(str(e))
            return self._handle_error(e, request, context)
    
    def _process_response(self, request, response, context: MiddlewareContext):
        """Process response with error handling."""
        try:
            return response
        except Exception as e:
            context.errors.append(str(e))
            return self._handle_error(e, request, context)
    
    def _handle_error(self, error: Exception, request, context: MiddlewareContext):
        """Handle errors with custom handlers."""
        error_type = type(error)
        
        # Try specific error handler
        if error_type in self.error_handlers:
            try:
                return self.error_handlers[error_type](error, request, context)
            except Exception:
                pass
        
        # Try parent class handlers
        for exc_type, handler in self.error_handlers.items():
            if isinstance(error, exc_type):
                try:
                    return handler(error, request, context)
                except Exception:
                    continue
        
        # Default error response
        from ..response import Response
        return Response.json(self.default_error_response, status=500)


class PerformanceMiddleware(BaseEnhancedMiddleware):
    """Performance monitoring middleware."""
    
    def __init__(self, config: MiddlewareConfig = None):
        """Initialize performance middleware."""
        super().__init__(config)
        self.slow_request_threshold = 1.0  # seconds
        self.memory_threshold = 100  # MB
        
    def _process_request(self, request, context: MiddlewareContext):
        """Start performance monitoring."""
        context.performance_metrics['request_start'] = time.time()
        context.performance_metrics['memory_start'] = self._get_memory_usage()
        return request
    
    def _process_response(self, request, response, context: MiddlewareContext):
        """End performance monitoring."""
        end_time = time.time()
        end_memory = self._get_memory_usage()
        
        duration = end_time - context.performance_metrics['request_start']
        memory_delta = end_memory - context.performance_metrics['memory_start']
        
        context.performance_metrics.update({
            'duration': duration,
            'memory_delta': memory_delta,
            'end_memory': end_memory
        })
        
        # Log slow requests
        if duration > self.slow_request_threshold:
            logging.warning(f"Slow request detected: {request.path} took {duration:.3f}s")
        
        # Log high memory usage
        if memory_delta > self.memory_threshold:
            logging.warning(f"High memory usage: {request.path} used {memory_delta:.1f}MB")
        
        return response
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0.0


class MiddlewareManager:
    """Enhanced middleware management system."""
    
    def __init__(self):
        """Initialize middleware manager."""
        self.middleware_stack = []
        self.middleware_stats = {}
        self._lock = threading.Lock()
    
    def add_middleware(self, middleware: BaseEnhancedMiddleware, priority: int = None):
        """Add middleware to the stack."""
        if priority is not None:
            middleware.config.priority = priority
        
        with self._lock:
            self.middleware_stack.append(middleware)
            # Sort by priority (higher priority first)
            self.middleware_stack.sort(key=lambda m: m.config.priority, reverse=True)
    
    def process_request(self, request, context: MiddlewareContext):
        """Process request through middleware stack."""
        for middleware in self.middleware_stack:
            try:
                request = middleware.process_request(request, context)
            except Exception as e:
                context.errors.append(f"{middleware.__class__.__name__}: {str(e)}")
                # Continue with other middleware
        
        return request
    
    def process_response(self, request, response, context: MiddlewareContext):
        """Process response through middleware stack (in reverse order)."""
        for middleware in reversed(self.middleware_stack):
            try:
                response = middleware.process_response(request, response, context)
            except Exception as e:
                context.errors.append(f"{middleware.__class__.__name__}: {str(e)}")
                # Continue with other middleware
        
        return response
    
    def get_middleware_stats(self) -> Dict[str, Any]:
        """Get statistics for all middleware."""
        with self._lock:
            stats = {}
            for middleware in self.middleware_stack:
                stats[middleware.__class__.__name__] = middleware.get_stats()
            return stats
    
    def remove_middleware(self, middleware_class: type):
        """Remove middleware by class type."""
        with self._lock:
            self.middleware_stack = [
                m for m in self.middleware_stack 
                if not isinstance(m, middleware_class)
            ]


# Global middleware manager instance
middleware_manager = MiddlewareManager()
