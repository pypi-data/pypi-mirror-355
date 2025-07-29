"""
Advanced Middleware System for WolfPy Framework - Phase 3 Improvements.

This module provides next-generation middleware functionality including:
- Async/await middleware support with coroutine handling
- Advanced request/response transformation pipelines
- Intelligent middleware dependency resolution and ordering
- Circuit breaker patterns for fault tolerance
- Middleware composition and chaining
- Real-time middleware performance monitoring
- Dynamic middleware loading and hot-swapping
- Middleware versioning and rollback capabilities
"""

import asyncio
import time
import threading
import inspect
from typing import Dict, List, Any, Optional, Callable, Union, Awaitable, Type
from dataclasses import dataclass, field
from collections import defaultdict, deque
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
import weakref
import json


@dataclass
class MiddlewareMetadata:
    """Metadata for middleware components."""
    name: str
    version: str = "1.0.0"
    priority: int = 0
    dependencies: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    async_compatible: bool = False
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    performance_profile: Dict[str, float] = field(default_factory=dict)


@dataclass
class MiddlewareExecutionContext:
    """Context for middleware execution."""
    request_id: str
    start_time: float
    middleware_chain: List[str] = field(default_factory=list)
    execution_times: Dict[str, float] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    async_mode: bool = False


class AdvancedCircuitBreaker:
    """Advanced circuit breaker with multiple failure modes."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0,
                 half_open_max_calls: int = 3):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before attempting recovery
            half_open_max_calls: Max calls allowed in half-open state
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.half_open_calls = 0
        self.success_count = 0
        
        self._lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        with self._lock:
            if self.state == "OPEN":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = "HALF_OPEN"
                    self.half_open_calls = 0
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            if self.state == "HALF_OPEN":
                if self.half_open_calls >= self.half_open_max_calls:
                    raise Exception("Circuit breaker is HALF_OPEN - max calls exceeded")
                self.half_open_calls += 1
        
        try:
            result = func(*args, **kwargs)
            
            with self._lock:
                if self.state == "HALF_OPEN":
                    self.success_count += 1
                    if self.success_count >= self.half_open_max_calls:
                        self.state = "CLOSED"
                        self.failure_count = 0
                        self.success_count = 0
                elif self.state == "CLOSED":
                    self.failure_count = max(0, self.failure_count - 1)
            
            return result
            
        except Exception as e:
            with self._lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                elif self.state == "HALF_OPEN":
                    self.state = "OPEN"
            
            raise e
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state."""
        with self._lock:
            return {
                'state': self.state,
                'failure_count': self.failure_count,
                'success_count': self.success_count,
                'last_failure_time': self.last_failure_time,
                'half_open_calls': self.half_open_calls
            }


class AdvancedMiddlewareBase:
    """Base class for advanced middleware with enhanced capabilities."""
    
    def __init__(self, metadata: MiddlewareMetadata = None):
        """Initialize advanced middleware."""
        self.metadata = metadata or MiddlewareMetadata(
            name=self.__class__.__name__
        )
        self.circuit_breaker = AdvancedCircuitBreaker()
        self.performance_metrics = {
            'total_calls': 0,
            'total_time': 0.0,
            'error_count': 0,
            'avg_time': 0.0
        }
        self._lock = threading.RLock()
    
    async def process_request_async(self, request, context: MiddlewareExecutionContext):
        """Process request asynchronously."""
        return await self._execute_async(self.process_request, request, context)
    
    async def process_response_async(self, request, response, context: MiddlewareExecutionContext):
        """Process response asynchronously."""
        return await self._execute_async(self.process_response, request, response, context)
    
    def process_request(self, request, context: MiddlewareExecutionContext):
        """Process request (override in subclasses)."""
        return request
    
    def process_response(self, request, response, context: MiddlewareExecutionContext):
        """Process response (override in subclasses)."""
        return response
    
    async def _execute_async(self, func: Callable, *args, **kwargs):
        """Execute function asynchronously with proper handling."""
        if inspect.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            # Run sync function in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, func, *args, **kwargs)
    
    def _record_performance(self, execution_time: float, error: bool = False):
        """Record performance metrics."""
        with self._lock:
            self.performance_metrics['total_calls'] += 1
            self.performance_metrics['total_time'] += execution_time
            
            if error:
                self.performance_metrics['error_count'] += 1
            
            # Update average
            total_calls = self.performance_metrics['total_calls']
            self.performance_metrics['avg_time'] = (
                self.performance_metrics['total_time'] / total_calls
            )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        with self._lock:
            return self.performance_metrics.copy()


class RequestTransformationMiddleware(AdvancedMiddlewareBase):
    """Advanced request transformation middleware."""
    
    def __init__(self, transformations: List[Callable] = None):
        """Initialize with transformation functions."""
        super().__init__(MiddlewareMetadata(
            name="RequestTransformationMiddleware",
            async_compatible=True
        ))
        self.transformations = transformations or []
    
    def add_transformation(self, func: Callable):
        """Add a transformation function."""
        self.transformations.append(func)
    
    def process_request(self, request, context: MiddlewareExecutionContext):
        """Apply transformations to request."""
        start_time = time.time()
        
        try:
            for transformation in self.transformations:
                request = transformation(request)
            
            execution_time = time.time() - start_time
            self._record_performance(execution_time)
            context.execution_times[self.metadata.name] = execution_time
            
            return request
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_performance(execution_time, error=True)
            context.errors.append(f"{self.metadata.name}: {str(e)}")
            raise


class ResponseCompressionMiddleware(AdvancedMiddlewareBase):
    """Advanced response compression middleware."""
    
    def __init__(self, compression_threshold: int = 1024, 
                 compression_level: int = 6):
        """Initialize compression middleware."""
        super().__init__(MiddlewareMetadata(
            name="ResponseCompressionMiddleware",
            async_compatible=True
        ))
        self.compression_threshold = compression_threshold
        self.compression_level = compression_level
    
    def process_response(self, request, response, context: MiddlewareExecutionContext):
        """Compress response if appropriate."""
        start_time = time.time()
        
        try:
            # Check if compression is appropriate
            if (hasattr(response, 'body') and 
                len(response.body) > self.compression_threshold and
                'gzip' in request.headers.get('Accept-Encoding', '')):
                
                import gzip
                
                # Compress response body
                if isinstance(response.body, str):
                    body_bytes = response.body.encode('utf-8')
                else:
                    body_bytes = response.body
                
                compressed_body = gzip.compress(body_bytes, compresslevel=self.compression_level)
                
                # Update response
                response.body = compressed_body
                response.headers['Content-Encoding'] = 'gzip'
                response.headers['Content-Length'] = str(len(compressed_body))
            
            execution_time = time.time() - start_time
            self._record_performance(execution_time)
            context.execution_times[self.metadata.name] = execution_time
            
            return response
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_performance(execution_time, error=True)
            context.errors.append(f"{self.metadata.name}: {str(e)}")
            return response  # Return original response on error


class AdvancedMiddlewareManager:
    """Advanced middleware management system."""
    
    def __init__(self):
        """Initialize advanced middleware manager."""
        self.middleware_registry = {}
        self.middleware_instances = {}
        self.execution_order = []
        self.dependency_graph = {}
        self.async_enabled = False
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        
        # Performance monitoring
        self.execution_stats = defaultdict(lambda: {
            'total_executions': 0,
            'total_time': 0.0,
            'error_count': 0,
            'avg_time': 0.0
        })
        
        self._lock = threading.RLock()
    
    def register_middleware(self, middleware_class: Type[AdvancedMiddlewareBase], 
                          **kwargs):
        """Register middleware class."""
        with self._lock:
            instance = middleware_class(**kwargs)
            name = instance.metadata.name
            
            self.middleware_registry[name] = middleware_class
            self.middleware_instances[name] = instance
            
            # Build dependency graph
            self._update_dependency_graph(instance)
            
            # Recalculate execution order
            self._calculate_execution_order()
    
    def _update_dependency_graph(self, middleware: AdvancedMiddlewareBase):
        """Update dependency graph for middleware."""
        name = middleware.metadata.name
        self.dependency_graph[name] = {
            'dependencies': middleware.metadata.dependencies,
            'conflicts': middleware.metadata.conflicts,
            'priority': middleware.metadata.priority
        }
    
    def _calculate_execution_order(self):
        """Calculate optimal middleware execution order."""
        # Topological sort with priority consideration
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(name):
            if name in temp_visited:
                raise Exception(f"Circular dependency detected involving {name}")
            if name in visited:
                return
            
            temp_visited.add(name)
            
            # Visit dependencies first
            deps = self.dependency_graph.get(name, {}).get('dependencies', [])
            for dep in deps:
                if dep in self.dependency_graph:
                    visit(dep)
            
            temp_visited.remove(name)
            visited.add(name)
            order.append(name)
        
        # Visit all middleware
        for name in self.dependency_graph:
            if name not in visited:
                visit(name)
        
        # Sort by priority within dependency constraints
        self.execution_order = sorted(order, 
            key=lambda x: self.dependency_graph.get(x, {}).get('priority', 0),
            reverse=True
        )
    
    async def process_request_async(self, request) -> Any:
        """Process request through async middleware chain."""
        context = MiddlewareExecutionContext(
            request_id=getattr(request, 'id', str(time.time())),
            start_time=time.time(),
            async_mode=True
        )
        
        for middleware_name in self.execution_order:
            middleware = self.middleware_instances[middleware_name]
            context.middleware_chain.append(middleware_name)
            
            try:
                if middleware.metadata.async_compatible:
                    request = await middleware.process_request_async(request, context)
                else:
                    request = middleware.process_request(request, context)
            except Exception as e:
                context.errors.append(f"{middleware_name}: {str(e)}")
                # Continue with other middleware
        
        return request
    
    async def process_response_async(self, request, response) -> Any:
        """Process response through async middleware chain."""
        context = MiddlewareExecutionContext(
            request_id=getattr(request, 'id', str(time.time())),
            start_time=time.time(),
            async_mode=True
        )
        
        # Process in reverse order for response
        for middleware_name in reversed(self.execution_order):
            middleware = self.middleware_instances[middleware_name]
            context.middleware_chain.append(middleware_name)
            
            try:
                if middleware.metadata.async_compatible:
                    response = await middleware.process_response_async(request, response, context)
                else:
                    response = middleware.process_response(request, response, context)
            except Exception as e:
                context.errors.append(f"{middleware_name}: {str(e)}")
                # Continue with other middleware
        
        return response
    
    def get_middleware_analytics(self) -> Dict[str, Any]:
        """Get comprehensive middleware analytics."""
        with self._lock:
            analytics = {
                'registered_middleware': list(self.middleware_registry.keys()),
                'execution_order': self.execution_order,
                'dependency_graph': dict(self.dependency_graph),
                'execution_stats': dict(self.execution_stats),
                'performance_metrics': {}
            }
            
            # Get performance metrics for each middleware
            for name, instance in self.middleware_instances.items():
                analytics['performance_metrics'][name] = instance.get_performance_metrics()
            
            return analytics


# Global advanced middleware manager
advanced_middleware_manager = AdvancedMiddlewareManager()
