"""
WolfPy Middleware Module.

This module provides enhanced middleware functionality for request/response processing.
Middleware allows you to process requests before they reach route handlers
and responses before they are sent to the client. Includes advanced features like
dependency management, performance monitoring, and circuit breaker patterns.
"""

import time
import logging
import asyncio
import threading
from collections import defaultdict, deque
from typing import List, Callable, Any, Dict, Optional, Union, Tuple
from .request import Request
from .response import Response


class MiddlewareGraph:
    """
    Dependency graph for middleware ordering and optimization.

    This class manages middleware dependencies and ensures proper execution order.
    """

    def __init__(self):
        self.nodes = {}  # middleware_name -> middleware_info
        self.dependencies = defaultdict(set)  # middleware -> set of dependencies
        self.dependents = defaultdict(set)  # middleware -> set of dependents

    def add_middleware(self, name: str, middleware: Callable,
                      dependencies: List[str] = None, priority: int = 0):
        """
        Add middleware with dependencies.

        Args:
            name: Middleware name
            middleware: Middleware callable
            dependencies: List of middleware names this depends on
            priority: Priority for ordering
        """
        self.nodes[name] = {
            'middleware': middleware,
            'priority': priority,
            'dependencies': dependencies or []
        }

        if dependencies:
            for dep in dependencies:
                self.dependencies[name].add(dep)
                self.dependents[dep].add(name)

    def get_execution_order(self) -> List[str]:
        """
        Get middleware execution order using topological sort.

        Returns:
            List of middleware names in execution order
        """
        # Kahn's algorithm for topological sorting
        in_degree = defaultdict(int)
        for node in self.nodes:
            in_degree[node] = len(self.dependencies[node])

        queue = deque([node for node in self.nodes if in_degree[node] == 0])
        result = []

        while queue:
            # Sort by priority for stable ordering
            current_level = []
            while queue:
                current_level.append(queue.popleft())

            current_level.sort(key=lambda x: self.nodes[x]['priority'], reverse=True)

            for node in current_level:
                result.append(node)

                for dependent in self.dependents[node]:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)

        if len(result) != len(self.nodes):
            raise ValueError("Circular dependency detected in middleware")

        return result


class MiddlewareProfiler:
    """
    Advanced profiler for middleware performance analysis.
    """

    def __init__(self):
        self.profiles = {}
        self.call_graph = defaultdict(list)
        self.bottlenecks = []

    def start_profile(self, middleware_name: str) -> str:
        """Start profiling a middleware execution."""
        profile_id = f"{middleware_name}_{time.time()}"
        self.profiles[profile_id] = {
            'name': middleware_name,
            'start_time': time.time(),
            'memory_start': self._get_memory_usage(),
            'cpu_start': time.process_time()
        }
        return profile_id

    def end_profile(self, profile_id: str):
        """End profiling and record results."""
        if profile_id not in self.profiles:
            return

        profile = self.profiles[profile_id]
        end_time = time.time()

        profile.update({
            'end_time': end_time,
            'duration': end_time - profile['start_time'],
            'memory_end': self._get_memory_usage(),
            'cpu_end': time.process_time(),
            'memory_delta': self._get_memory_usage() - profile['memory_start'],
            'cpu_time': time.process_time() - profile['cpu_start']
        })

        # Detect bottlenecks (>100ms execution time)
        if profile['duration'] > 0.1:
            self.bottlenecks.append(profile)

    def _get_memory_usage(self) -> int:
        """Get current memory usage (simplified)."""
        try:
            import psutil
            return psutil.Process().memory_info().rss
        except ImportError:
            return 0

    def get_bottlenecks(self) -> List[Dict[str, Any]]:
        """Get detected performance bottlenecks."""
        return sorted(self.bottlenecks, key=lambda x: x['duration'], reverse=True)


class CircuitBreaker:
    """
    Circuit breaker pattern for middleware fault tolerance.
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN

    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            if self.state == 'HALF_OPEN':
                self.state = 'CLOSED'
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = 'OPEN'

            raise e


class BaseMiddleware:
    """
    Base middleware class with lifecycle hooks.

    Provides a structured way to create middleware with proper
    initialization, request/response processing, and cleanup.
    """

    def __init__(self, **kwargs):
        """Initialize middleware with configuration."""
        self.config = kwargs
        self.enabled = kwargs.get('enabled', True)
        self.priority = kwargs.get('priority', 0)  # Higher priority runs first

    def process_request(self, request: Request) -> Optional[Request]:
        """
        Process incoming request.

        Args:
            request: The incoming request

        Returns:
            Modified request or None to continue with original
        """
        return None

    def process_response(self, request: Request, response: Response) -> Optional[Response]:
        """
        Process outgoing response.

        Args:
            request: The original request
            response: The response to process

        Returns:
            Modified response or None to continue with original
        """
        return None

    def process_exception(self, request: Request, exception: Exception) -> Optional[Response]:
        """
        Process exceptions that occur during request handling.

        Args:
            request: The original request
            exception: The exception that occurred

        Returns:
            Response to return or None to continue with default handling
        """
        return None

    def __call__(self, request: Request, response: Response = None) -> Union[Request, Response]:
        """Make middleware callable for backward compatibility."""
        if response is None:
            # Request processing
            result = self.process_request(request)
            return result if result is not None else request
        else:
            # Response processing
            result = self.process_response(request, response)
            return result if result is not None else response


class MiddlewareStack:
    """
    Advanced middleware stack with ordering and exception handling.
    """

    def __init__(self):
        """Initialize middleware stack."""
        self.middleware_instances = []
        self.request_middleware = []
        self.response_middleware = []
        self.exception_middleware = []

    def add(self, middleware: Union[Callable, BaseMiddleware], priority: int = 0):
        """
        Add middleware to the stack.

        Args:
            middleware: Middleware function or instance
            priority: Priority for ordering (higher runs first)
        """
        if isinstance(middleware, BaseMiddleware):
            if middleware.enabled:
                self.middleware_instances.append(middleware)
                self._rebuild_stacks()
        else:
            # Legacy middleware function
            self._add_legacy_middleware(middleware, priority)

    def _add_legacy_middleware(self, middleware_func: Callable, priority: int):
        """Add legacy middleware function."""
        import inspect

        if hasattr(middleware_func, 'process_request'):
            self.request_middleware.append((priority, middleware_func.process_request))
        elif hasattr(middleware_func, '__call__'):
            sig = inspect.signature(middleware_func)
            params = list(sig.parameters.keys())

            if len(params) == 1:
                self.request_middleware.append((priority, middleware_func))
            elif len(params) == 2:
                self.response_middleware.append((priority, middleware_func))

        if hasattr(middleware_func, 'process_response'):
            self.response_middleware.append((priority, middleware_func.process_response))

        # Sort by priority
        self.request_middleware.sort(key=lambda x: x[0], reverse=True)
        self.response_middleware.sort(key=lambda x: x[0], reverse=True)

    def _rebuild_stacks(self):
        """Rebuild middleware stacks from instances."""
        self.request_middleware = []
        self.response_middleware = []
        self.exception_middleware = []

        # Sort instances by priority
        sorted_instances = sorted(self.middleware_instances,
                                key=lambda x: x.priority, reverse=True)

        for instance in sorted_instances:
            if hasattr(instance, 'process_request'):
                self.request_middleware.append((instance.priority, instance.process_request))
            if hasattr(instance, 'process_response'):
                self.response_middleware.append((instance.priority, instance.process_response))
            if hasattr(instance, 'process_exception'):
                self.exception_middleware.append((instance.priority, instance.process_exception))


class Middleware(MiddlewareStack):
    """
    Middleware manager for FoxPy applications.
    
    Handles the middleware pipeline for processing requests and responses.
    Middleware functions are executed in the order they are added.
    """
    
    def __init__(self):
        """Initialize the enhanced middleware manager."""
        # Initialize parent class attributes first
        self.middleware_instances = []
        self._request_middleware = []
        self._response_middleware = []
        self.exception_middleware = []

        # Keep legacy attributes for backward compatibility
        self._legacy_request_middleware = []
        self._legacy_response_middleware = []

        # Performance monitoring
        self._middleware_stats = {}
        self._total_requests = 0
        self._error_count = 0
        self._performance_enabled = True

        # Enhanced error handling
        self._error_handlers = {}
        self._fallback_error_handler = None

        # Advanced middleware features
        self._middleware_graph = MiddlewareGraph()  # Dependency graph
        self._async_middleware = []  # Async middleware support
        self._middleware_pools = {}  # Middleware pools for load balancing
        self._conditional_middleware = {}  # Conditional middleware execution
        self._middleware_circuit_breakers = {}  # Circuit breaker pattern

        # Advanced performance features
        self._middleware_profiler = MiddlewareProfiler()
        self._middleware_cache = {}  # Middleware result caching
        self._middleware_composition_cache = {}  # Composed middleware cache

        # Async middleware support
        self._async_executor = None
        self._async_enabled = False

        # Middleware health monitoring
        self._middleware_health = {}
        self._health_check_interval = 60  # seconds
        self._last_health_check = time.time()

        # Advanced caching and optimization
        self._middleware_result_cache = {}
        self._cache_enabled = True
        self._cache_ttl = 300  # 5 minutes

        # Thread safety
        self._lock = threading.RLock()

    def add(self, middleware_func: Callable, priority: int = 0):
        """
        Add middleware to the pipeline with enhanced features.

        Args:
            middleware_func: Middleware function or class
            priority: Priority for ordering (higher runs first)
        """
        if isinstance(middleware_func, BaseMiddleware):
            if middleware_func.enabled:
                self.middleware_instances.append(middleware_func)

                # Override priority with the one passed to add() method
                middleware_func.priority = priority

                # Add to priority-ordered lists
                if hasattr(middleware_func, 'process_request'):
                    self._request_middleware.append((priority, middleware_func.process_request))
                if hasattr(middleware_func, 'process_response'):
                    self._response_middleware.append((priority, middleware_func.process_response))
                if hasattr(middleware_func, 'process_exception'):
                    self.exception_middleware.append((priority, middleware_func.process_exception))

                # Sort by priority (higher priority first)
                self._request_middleware.sort(key=lambda x: x[0], reverse=True)
                self._response_middleware.sort(key=lambda x: x[0], reverse=True)
                self.exception_middleware.sort(key=lambda x: x[0], reverse=True)
        else:
            # Legacy middleware handling - also support priority
            if hasattr(middleware_func, 'process_request'):
                self._request_middleware.append((priority, middleware_func.process_request))
            elif hasattr(middleware_func, '__call__'):
                import inspect
                sig = inspect.signature(middleware_func)
                params = list(sig.parameters.keys())

                if len(params) == 1:
                    self._request_middleware.append((priority, middleware_func))
                elif len(params) == 2:
                    self._response_middleware.append((priority, middleware_func))

            if hasattr(middleware_func, 'process_response'):
                self._response_middleware.append((priority, middleware_func.process_response))

            # Sort by priority
            self._request_middleware.sort(key=lambda x: x[0], reverse=True)
            self._response_middleware.sort(key=lambda x: x[0], reverse=True)

    @property
    def request_middleware(self):
        """Get request middleware for backward compatibility."""
        return [mw[1] for mw in self._request_middleware] + self._legacy_request_middleware

    @property
    def response_middleware(self):
        """Get response middleware for backward compatibility."""
        return [mw[1] for mw in self._response_middleware] + self._legacy_response_middleware
    
    def process_request(self, request: Request) -> Request:
        """
        Process request through all request middleware with enhanced error handling.

        Args:
            request: The incoming request

        Returns:
            Modified request object
        """
        # Process through priority-ordered middleware
        for priority, middleware in self._request_middleware:
            try:
                result = middleware(request)
                if result is not None:
                    request = result
            except Exception as e:
                # Try exception middleware first
                handled = self._handle_exception(request, e)
                if handled:
                    return handled
                # Log the error and continue
                print(f"Error in request middleware: {e}")

        # Process conditional middleware
        for name, config in self._conditional_middleware.items():
            try:
                if config['condition'](request):
                    result = config['middleware'](request)
                    if result is not None:
                        request = result
            except Exception as e:
                print(f"Error in conditional middleware {name}: {e}")

        # Process legacy middleware for backward compatibility
        for middleware in self._legacy_request_middleware:
            try:
                result = middleware(request)
                if result is not None:
                    request = result
            except Exception as e:
                print(f"Error in legacy request middleware: {e}")

        return request

    def process_response(self, request: Request, response: Response) -> Response:
        """
        Process response through all response middleware with enhanced error handling.

        Args:
            request: The original request
            response: The response to process

        Returns:
            Modified response object
        """
        # Process through priority-ordered middleware
        for priority, middleware in self._response_middleware:
            try:
                result = middleware(request, response)
                if result is not None:
                    response = result
            except Exception as e:
                # Try exception middleware first
                handled = self._handle_exception(request, e)
                if handled:
                    return handled
                # Log the error and continue
                print(f"Error in response middleware: {e}")

        # Process legacy middleware for backward compatibility
        for middleware in self._legacy_response_middleware:
            try:
                result = middleware(request, response)
                if result is not None:
                    response = result
            except Exception as e:
                print(f"Error in legacy response middleware: {e}")

        return response

    def add_dependency_middleware(self, name: str, middleware: Callable,
                                dependencies: List[str] = None, priority: int = 0):
        """
        Add middleware with dependency management.

        Args:
            name: Middleware name
            middleware: Middleware callable
            dependencies: List of middleware names this depends on
            priority: Priority for ordering
        """
        self._middleware_graph.add_middleware(name, middleware, dependencies, priority)

        # Rebuild execution order
        execution_order = self._middleware_graph.get_execution_order()

        # Clear and rebuild middleware lists
        self._request_middleware = []
        self._response_middleware = []

        for middleware_name in execution_order:
            middleware_info = self._middleware_graph.nodes[middleware_name]
            middleware_func = middleware_info['middleware']
            priority = middleware_info['priority']

            if hasattr(middleware_func, 'process_request'):
                self._request_middleware.append((priority, middleware_func.process_request))
            if hasattr(middleware_func, 'process_response'):
                self._response_middleware.append((priority, middleware_func.process_response))

    def add_conditional_middleware(self, name: str, middleware: Callable,
                                 condition: Callable[[Request], bool]):
        """
        Add middleware that only executes when condition is met.

        Args:
            name: Middleware name
            middleware: Middleware callable
            condition: Function that takes request and returns bool
        """
        self._conditional_middleware[name] = {
            'middleware': middleware,
            'condition': condition
        }

    def add_circuit_breaker(self, middleware_name: str, failure_threshold: int = 5,
                          recovery_timeout: int = 60):
        """
        Add circuit breaker protection to middleware.

        Args:
            middleware_name: Name of middleware to protect
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before attempting recovery
        """
        self._middleware_circuit_breakers[middleware_name] = CircuitBreaker(
            failure_threshold, recovery_timeout
        )

    def _handle_exception(self, request: Request, exception: Exception) -> Optional[Response]:
        """Handle exceptions through exception middleware."""
        for priority, middleware in self.exception_middleware:
            try:
                result = middleware(request, exception)
                if result is not None:
                    return result
            except Exception as e:
                print(f"Error in exception middleware: {e}")
        return None

    def record_middleware_stats(self, middleware_name: str, execution_time: float, success: bool = True):
        """
        Record middleware performance statistics.

        Args:
            middleware_name: Name of the middleware
            execution_time: Time taken to execute
            success: Whether the middleware executed successfully
        """
        if not self._performance_enabled:
            return

        if middleware_name not in self._middleware_stats:
            self._middleware_stats[middleware_name] = {
                'total_time': 0.0,
                'call_count': 0,
                'error_count': 0,
                'avg_time': 0.0,
                'max_time': 0.0,
                'min_time': float('inf')
            }

        stats = self._middleware_stats[middleware_name]
        stats['total_time'] += execution_time
        stats['call_count'] += 1

        if not success:
            stats['error_count'] += 1

        stats['avg_time'] = stats['total_time'] / stats['call_count']
        stats['max_time'] = max(stats['max_time'], execution_time)
        stats['min_time'] = min(stats['min_time'], execution_time)

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get middleware performance statistics.

        Returns:
            Dictionary containing performance metrics
        """
        return {
            'total_requests': self._total_requests,
            'error_count': self._error_count,
            'middleware_stats': self._middleware_stats.copy(),
            'performance_enabled': self._performance_enabled
        }

    def enable_performance_monitoring(self):
        """Enable performance monitoring."""
        self._performance_enabled = True

    def disable_performance_monitoring(self):
        """Disable performance monitoring."""
        self._performance_enabled = False

    def reset_stats(self):
        """Reset all performance statistics."""
        self._middleware_stats.clear()
        self._total_requests = 0
        self._error_count = 0

    def add_conditional_middleware(self, middleware: Callable, condition: Callable,
                                 priority: int = 0, name: str = None):
        """
        Add middleware that only executes when condition is met.

        Args:
            middleware: Middleware function
            condition: Function that takes request and returns bool
            priority: Execution priority
            name: Optional middleware name
        """
        middleware_name = name or f"conditional_{len(self._conditional_middleware)}"
        self._conditional_middleware[middleware_name] = {
            'middleware': middleware,
            'condition': condition,
            'priority': priority
        }

    def add_async_middleware(self, middleware: Callable, priority: int = 0):
        """
        Add async middleware for concurrent execution.

        Args:
            middleware: Async middleware function
            priority: Execution priority
        """
        self._async_middleware.append((priority, middleware))
        self._async_middleware.sort(key=lambda x: x[0], reverse=True)

    def compose_middleware(self, middleware_list: List[Callable],
                          name: str = None) -> Callable:
        """
        Compose multiple middleware into a single middleware function.

        Args:
            middleware_list: List of middleware functions to compose
            name: Optional name for the composed middleware

        Returns:
            Composed middleware function
        """
        composition_key = name or f"composed_{hash(tuple(middleware_list))}"

        if composition_key in self._middleware_composition_cache:
            return self._middleware_composition_cache[composition_key]

        def composed_middleware(request: Request) -> Optional[Request]:
            current_request = request
            for middleware in middleware_list:
                try:
                    result = middleware(current_request)
                    if result is not None:
                        current_request = result
                except Exception as e:
                    print(f"Error in composed middleware: {e}")
                    break
            return current_request

        self._middleware_composition_cache[composition_key] = composed_middleware
        return composed_middleware

    def add_circuit_breaker(self, middleware_name: str, failure_threshold: int = 5,
                           recovery_timeout: int = 60):
        """
        Add circuit breaker protection to middleware.

        Args:
            middleware_name: Name of middleware to protect
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds before attempting recovery
        """
        self._middleware_circuit_breakers[middleware_name] = CircuitBreaker(
            failure_threshold, recovery_timeout
        )

    def get_advanced_performance_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive middleware performance statistics.

        Returns:
            Dictionary with detailed performance metrics
        """
        basic_stats = self.get_performance_stats()

        return {
            **basic_stats,
            'bottlenecks': self._middleware_profiler.get_bottlenecks(),
            'circuit_breaker_states': {
                name: breaker.state
                for name, breaker in self._middleware_circuit_breakers.items()
            },
            'conditional_middleware_count': len(self._conditional_middleware),
            'async_middleware_count': len(self._async_middleware),
            'composed_middleware_count': len(self._middleware_composition_cache),
            'dependency_graph_size': len(self._middleware_graph.nodes)
        }


class MiddlewareProfiler:
    """
    Middleware performance profiler.
    """

    def __init__(self):
        """Initialize profiler."""
        self.profiles = {}
        self.enabled = False

    def enable(self):
        """Enable profiling."""
        self.enabled = True

    def disable(self):
        """Disable profiling."""
        self.enabled = False

    def profile_middleware(self, middleware_name: str, execution_time: float):
        """
        Record middleware execution time.

        Args:
            middleware_name: Name of the middleware
            execution_time: Time taken to execute
        """
        if not self.enabled:
            return

        if middleware_name not in self.profiles:
            self.profiles[middleware_name] = {
                'total_time': 0.0,
                'call_count': 0,
                'avg_time': 0.0,
                'max_time': 0.0,
                'min_time': float('inf')
            }

        profile = self.profiles[middleware_name]
        profile['total_time'] += execution_time
        profile['call_count'] += 1
        profile['avg_time'] = profile['total_time'] / profile['call_count']
        profile['max_time'] = max(profile['max_time'], execution_time)
        profile['min_time'] = min(profile['min_time'], execution_time)

    def get_stats(self) -> Dict[str, Any]:
        """Get profiling statistics."""
        return self.profiles.copy()

    def get_bottlenecks(self, threshold: float = 0.1) -> List[Dict[str, Any]]:
        """
        Get middleware bottlenecks (slow middleware).

        Args:
            threshold: Minimum average time to be considered a bottleneck

        Returns:
            List of bottleneck middleware sorted by average time
        """
        bottlenecks = []
        for name, profile in self.profiles.items():
            if profile['avg_time'] >= threshold:
                bottlenecks.append({
                    'name': name,
                    'avg_time': profile['avg_time'],
                    'max_time': profile['max_time'],
                    'call_count': profile['call_count'],
                    'total_time': profile['total_time']
                })

        # Sort by average time (descending)
        bottlenecks.sort(key=lambda x: x['avg_time'], reverse=True)
        return bottlenecks

    def reset(self):
        """Reset profiling data."""
        self.profiles.clear()


class MiddlewareComposer:
    """
    Middleware composition utilities for creating complex middleware chains.
    """

    @staticmethod
    def compose(*middlewares):
        """
        Compose multiple middleware into a single middleware.

        Args:
            *middlewares: Middleware functions or classes

        Returns:
            Composed middleware function
        """
        def composed_middleware(request, response=None):
            if response is None:
                # Request processing
                for middleware in middlewares:
                    if hasattr(middleware, 'process_request'):
                        result = middleware.process_request(request)
                        if result is not None:
                            request = result
                    elif callable(middleware):
                        result = middleware(request)
                        if result is not None:
                            request = result
                return request
            else:
                # Response processing (reverse order)
                for middleware in reversed(middlewares):
                    if hasattr(middleware, 'process_response'):
                        result = middleware.process_response(request, response)
                        if result is not None:
                            response = result
                    elif callable(middleware):
                        result = middleware(request, response)
                        if result is not None:
                            response = result
                return response

        return composed_middleware

    @staticmethod
    def conditional(condition_func, middleware):
        """
        Create conditional middleware that only runs when condition is met.

        Args:
            condition_func: Function that takes request and returns bool
            middleware: Middleware to run conditionally

        Returns:
            Conditional middleware
        """
        class ConditionalMiddleware(BaseMiddleware):
            def process_request(self, request):
                if condition_func(request):
                    if hasattr(middleware, 'process_request'):
                        return middleware.process_request(request)
                    elif callable(middleware):
                        return middleware(request)
                return None

            def process_response(self, request, response):
                if condition_func(request):
                    if hasattr(middleware, 'process_response'):
                        return middleware.process_response(request, response)
                    elif callable(middleware):
                        return middleware(request, response)
                return None

        return ConditionalMiddleware()


# Advanced middleware classes

class RequestValidationMiddleware(BaseMiddleware):
    """
    Request validation middleware with comprehensive validation rules.
    """

    def __init__(self, validation_rules: Dict[str, Dict] = None, **kwargs):
        """
        Initialize validation middleware.

        Args:
            validation_rules: Dictionary of validation rules per route
        """
        super().__init__(**kwargs)
        self.validation_rules = validation_rules or {}

    def process_request(self, request: Request) -> Optional[Request]:
        """Validate request data."""
        route_rules = self.validation_rules.get(request.path, {})
        if not route_rules:
            return None

        errors = {}

        # Validate JSON data
        if 'json_schema' in route_rules and request.is_json():
            json_errors = request.validate_json_schema(route_rules['json_schema'])
            if json_errors:
                errors.update(json_errors)

        # Validate form data
        if 'form_rules' in route_rules and request.method in ('POST', 'PUT', 'PATCH'):
            form_rules = route_rules['form_rules']
            for field, rules in form_rules.items():
                value = request.get_form(field)

                if rules.get('required', False) and not value:
                    errors.setdefault(field, []).append(f'{field} is required')

                if value and 'validator' in rules:
                    if not rules['validator'](value):
                        errors.setdefault(field, []).append(f'{field} is invalid')

        # Store validation errors in request context
        if errors:
            request.set_context('validation_errors', errors)

        return None


class RateLimitMiddleware(BaseMiddleware):
    """
    Rate limiting middleware to prevent abuse.
    """

    def __init__(self, requests_per_minute: int = 60, **kwargs):
        """
        Initialize rate limiting middleware.

        Args:
            requests_per_minute: Maximum requests per minute per IP
        """
        super().__init__(**kwargs)
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}  # In production, use Redis or similar

    def process_request(self, request: Request) -> Optional[Response]:
        """Check rate limits."""
        client_ip = request.remote_addr
        current_time = time.time()

        # Clean old entries (older than 1 minute)
        cutoff_time = current_time - 60
        self.request_counts = {
            ip: [(timestamp, count) for timestamp, count in requests
                 if timestamp > cutoff_time]
            for ip, requests in self.request_counts.items()
        }

        # Count requests for this IP in the last minute
        ip_requests = self.request_counts.get(client_ip, [])
        total_requests = sum(count for timestamp, count in ip_requests)

        if total_requests >= self.requests_per_minute:
            from .response import Response
            return Response(
                "Rate limit exceeded. Please try again later.",
                status=429,
                headers={
                    'Retry-After': '60',
                    'X-RateLimit-Limit': str(self.requests_per_minute),
                    'X-RateLimit-Remaining': '0'
                }
            )

        # Record this request
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        self.request_counts[client_ip].append((current_time, 1))

        return None


class RequestTimingMiddleware(BaseMiddleware):
    """
    Request timing middleware for performance monitoring.
    """

    def __init__(self, **kwargs):
        """Initialize timing middleware."""
        super().__init__(**kwargs)

    def process_request(self, request: Request) -> Optional[Request]:
        """Record request start time."""
        request.set_context('start_time', time.time())
        return None

    def process_response(self, request: Request, response: Response) -> Optional[Response]:
        """Add timing information to response."""
        start_time = request.get_context('start_time')
        if start_time:
            duration = time.time() - start_time
            response.set_header('X-Response-Time', f'{duration:.3f}s')
            request.set_context('response_time', duration)
        return None


class CSRFProtectionMiddleware(BaseMiddleware):
    """
    CSRF protection middleware.
    """

    def __init__(self, secret_key: str = None, **kwargs):
        """
        Initialize CSRF protection middleware.

        Args:
            secret_key: Secret key for token generation
        """
        super().__init__(**kwargs)
        self.secret_key = secret_key or 'default-csrf-secret'
        self.safe_methods = {'GET', 'HEAD', 'OPTIONS', 'TRACE'}

    def generate_token(self, request) -> str:
        """Generate CSRF token for request."""
        import hmac
        import secrets

        # Use session ID or IP as base
        base = request.get_context('session_id', request.remote_addr)
        nonce = secrets.token_urlsafe(16)

        # Create HMAC token
        message = f"{base}:{nonce}".encode()
        signature = hmac.new(self.secret_key.encode(), message, 'sha256').hexdigest()

        return f"{nonce}:{signature}"

    def validate_token(self, request, token: str) -> bool:
        """Validate CSRF token."""
        if not token or ':' not in token:
            return False

        try:
            nonce, signature = token.split(':', 1)
            base = request.get_context('session_id', request.remote_addr)

            import hmac
            message = f"{base}:{nonce}".encode()
            expected = hmac.new(self.secret_key.encode(), message, 'sha256').hexdigest()

            return hmac.compare_digest(signature, expected)
        except Exception:
            return False

    def process_request(self, request):
        """Process request for CSRF protection."""
        # Generate token for all requests
        token = self.generate_token(request)
        request.set_context('csrf_token', token)

        # Validate token for unsafe methods
        if request.method not in self.safe_methods:
            submitted_token = (
                request.get_form('csrf_token') or
                request.get_header('X-CSRF-Token') or
                request.get_cookie('csrf_token')
            )

            if not self.validate_token(request, submitted_token):
                from .response import Response
                return Response("CSRF token validation failed", status=403)

        return None


class CORSMiddleware(BaseMiddleware):
    """
    CORS (Cross-Origin Resource Sharing) middleware.
    """

    def __init__(self, allowed_origins: List[str] = None,
                 allowed_methods: List[str] = None,
                 allowed_headers: List[str] = None,
                 allow_credentials: bool = False,
                 max_age: int = 86400, **kwargs):
        """
        Initialize CORS middleware.

        Args:
            allowed_origins: List of allowed origins
            allowed_methods: List of allowed HTTP methods
            allowed_headers: List of allowed headers
            allow_credentials: Whether to allow credentials
            max_age: Max age for preflight cache
        """
        super().__init__(**kwargs)
        self.allowed_origins = allowed_origins or ['*']
        self.allowed_methods = allowed_methods or ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
        self.allowed_headers = allowed_headers or ['Content-Type', 'Authorization']
        self.allow_credentials = allow_credentials
        self.max_age = max_age

    def process_request(self, request):
        """Handle CORS preflight requests."""
        if request.method == 'OPTIONS':
            from .response import Response
            return self._create_preflight_response(request)
        return None

    def process_response(self, request, response):
        """Add CORS headers to response."""
        origin = request.get_header('Origin')

        if origin and self._is_origin_allowed(origin):
            response.set_header('Access-Control-Allow-Origin', origin)
        elif '*' in self.allowed_origins:
            response.set_header('Access-Control-Allow-Origin', '*')

        if self.allow_credentials:
            response.set_header('Access-Control-Allow-Credentials', 'true')

        return None

    def _is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is allowed."""
        return '*' in self.allowed_origins or origin in self.allowed_origins

    def _create_preflight_response(self, request):
        """Create preflight response."""
        from .response import Response

        response = Response('', status=200)
        origin = request.get_header('Origin')

        if origin and self._is_origin_allowed(origin):
            response.set_header('Access-Control-Allow-Origin', origin)
            response.set_header('Access-Control-Allow-Methods', ', '.join(self.allowed_methods))
            response.set_header('Access-Control-Allow-Headers', ', '.join(self.allowed_headers))
            response.set_header('Access-Control-Max-Age', str(self.max_age))

            if self.allow_credentials:
                response.set_header('Access-Control-Allow-Credentials', 'true')

        return response


class CompressionMiddleware(BaseMiddleware):
    """
    Response compression middleware.
    """

    def __init__(self, min_size: int = 1024, compression_level: int = 6, **kwargs):
        """
        Initialize compression middleware.

        Args:
            min_size: Minimum response size to compress
            compression_level: Gzip compression level (1-9)
        """
        super().__init__(**kwargs)
        self.min_size = min_size
        self.compression_level = compression_level
        self.compressible_types = {
            'text/html', 'text/css', 'text/javascript', 'text/plain',
            'application/json', 'application/javascript', 'application/xml'
        }

    def process_response(self, request, response):
        """Compress response if appropriate."""
        # Check if client accepts gzip
        accept_encoding = request.get_header('Accept-Encoding', '')
        if 'gzip' not in accept_encoding:
            return None

        # Check response size
        if len(response.body) < self.min_size:
            return None

        # Check content type
        content_type = response.headers.get('Content-Type', '').split(';')[0]
        if content_type not in self.compressible_types:
            return None

        # Compress response
        import gzip
        if isinstance(response.body, str):
            body_bytes = response.body.encode('utf-8')
        else:
            body_bytes = response.body

        compressed = gzip.compress(body_bytes, compresslevel=self.compression_level)

        # Update response
        response.body = compressed
        response.set_header('Content-Encoding', 'gzip')
        response.set_header('Content-Length', str(len(compressed)))

        return None


# Built-in middleware classes

class SessionMiddleware(BaseMiddleware):
    """
    Session middleware for automatic session handling.
    """

    def __init__(self, session_manager, **kwargs):
        """
        Initialize session middleware.

        Args:
            session_manager: Session manager instance
        """
        super().__init__(**kwargs)
        self.session_manager = session_manager

    def process_request(self, request):
        """Load session from request."""
        session = self.session_manager.load_session(request)
        request.session = session
        return None

    def process_response(self, request, response):
        """Save session to response."""
        if hasattr(request, 'session'):
            self.session_manager.save_session(request.session, response)
        return None


class AuthenticationMiddleware(BaseMiddleware):
    """
    Authentication middleware for automatic user loading.
    """

    def __init__(self, auth_manager, **kwargs):
        """
        Initialize authentication middleware.

        Args:
            auth_manager: Auth manager instance
        """
        super().__init__(**kwargs)
        self.auth_manager = auth_manager

    def process_request(self, request):
        """Load current user from request."""
        user = self.auth_manager.get_current_user(request)
        request.user = user
        request.is_authenticated = user is not None
        return None


class SecurityHeadersMiddleware:
    """
    Security headers middleware.

    Adds common security headers to responses.
    """

    def __init__(self,
                 content_security_policy: str = None,
                 x_frame_options: str = 'DENY',
                 x_content_type_options: str = 'nosniff',
                 x_xss_protection: str = '1; mode=block',
                 strict_transport_security: str = None):
        """
        Initialize security headers middleware.

        Args:
            content_security_policy: CSP header value
            x_frame_options: X-Frame-Options header value
            x_content_type_options: X-Content-Type-Options header value
            x_xss_protection: X-XSS-Protection header value
            strict_transport_security: HSTS header value
        """
        self.csp = content_security_policy
        self.x_frame_options = x_frame_options
        self.x_content_type_options = x_content_type_options
        self.x_xss_protection = x_xss_protection
        self.hsts = strict_transport_security

    def process_response(self, request: Request, response: Response) -> Response:
        """Add security headers to the response."""
        if self.csp:
            response.set_header('Content-Security-Policy', self.csp)

        if self.x_frame_options:
            response.set_header('X-Frame-Options', self.x_frame_options)

        if self.x_content_type_options:
            response.set_header('X-Content-Type-Options', self.x_content_type_options)

        if self.x_xss_protection:
            response.set_header('X-XSS-Protection', self.x_xss_protection)

        if self.hsts and request.environ.get('wsgi.url_scheme') == 'https':
            response.set_header('Strict-Transport-Security', self.hsts)

        return response


class LoggingMiddleware:
    """
    Request logging middleware.

    Logs incoming requests and their responses.
    """

    def __init__(self, logger=None):
        """
        Initialize logging middleware.

        Args:
            logger: Logger instance (uses print if None)
        """
        self.logger = logger

    def process_request(self, request: Request) -> Request:
        """Log the incoming request."""
        log_msg = f"{request.method} {request.path} - {request.remote_addr}"
        if self.logger:
            self.logger.info(log_msg)
        else:
            print(f"[REQUEST] {log_msg}")
        return request

    def process_response(self, request: Request, response: Response) -> Response:
        """Log the response."""
        log_msg = f"{request.method} {request.path} - {response.status} {response.status_text}"
        if self.logger:
            self.logger.info(log_msg)
        else:
            print(f"[RESPONSE] {log_msg}")
        return response


class ContentNegotiationMiddleware(BaseMiddleware):
    """
    Middleware for automatic content negotiation based on Accept headers.
    """

    def __init__(self, default_content_type: str = 'application/json', **kwargs):
        super().__init__(**kwargs)
        self.default_content_type = default_content_type
        self.supported_types = {
            'application/json': 'json',
            'application/xml': 'xml',
            'text/html': 'html',
            'text/plain': 'text',
            'text/csv': 'csv'
        }

    def process_request(self, request: Request) -> Optional[Request]:
        """Negotiate content type based on Accept header."""
        accept_types = request.accept_types

        # Find best matching content type
        best_match = None
        for accept_type in accept_types:
            media_type = accept_type['media_type']
            if media_type in self.supported_types:
                best_match = media_type
                break
            elif media_type == '*/*':
                best_match = self.default_content_type
                break

        if not best_match:
            best_match = self.default_content_type

        # Set negotiated content type in request context
        request.set_context('negotiated_content_type', best_match)
        request.set_context('response_format', self.supported_types.get(best_match, 'json'))

        return request


class RequestTransformationMiddleware(BaseMiddleware):
    """
    Middleware for transforming request data (normalization, validation, etc.).
    """

    def __init__(self, transformations: Dict[str, Callable] = None, **kwargs):
        super().__init__(**kwargs)
        self.transformations = transformations or {}
        self.default_transformations = {
            'normalize_headers': self._normalize_headers,
            'sanitize_query_params': self._sanitize_query_params,
            'validate_content_length': self._validate_content_length
        }

    def process_request(self, request: Request) -> Optional[Request]:
        """Apply transformations to request."""
        # Apply default transformations
        for name, transform_func in self.default_transformations.items():
            try:
                transform_func(request)
            except Exception as e:
                print(f"Error in transformation {name}: {e}")

        # Apply custom transformations
        for name, transform_func in self.transformations.items():
            try:
                transform_func(request)
            except Exception as e:
                print(f"Error in custom transformation {name}: {e}")

        return request

    def _normalize_headers(self, request: Request):
        """Normalize header names to lowercase."""
        # Headers are already normalized in WSGI environ
        pass

    def _sanitize_query_params(self, request: Request):
        """Sanitize query parameters."""
        # Add basic XSS protection
        for key, values in request.args.items():
            if isinstance(values, list):
                for i, value in enumerate(values):
                    if isinstance(value, str):
                        # Basic HTML entity encoding
                        values[i] = value.replace('<', '&lt;').replace('>', '&gt;')

    def _validate_content_length(self, request: Request):
        """Validate content length against limits."""
        content_length = request.content_length
        max_size = 50 * 1024 * 1024  # 50MB

        if content_length and content_length > max_size:
            raise ValueError(f"Request too large: {content_length} bytes")


class ResponseCompressionMiddleware(BaseMiddleware):
    """
    Middleware for compressing responses based on Accept-Encoding header.
    """

    def __init__(self, compression_level: int = 6, min_size: int = 1024, **kwargs):
        super().__init__(**kwargs)
        self.compression_level = compression_level
        self.min_size = min_size
        self.compressible_types = {
            'text/html', 'text/plain', 'text/css', 'text/javascript',
            'application/json', 'application/xml', 'application/javascript'
        }

    def process_response(self, request: Request, response: Response) -> Optional[Response]:
        """Compress response if appropriate."""
        # Check if client accepts compression
        accept_encoding = request.get_header('Accept-Encoding', '')
        if 'gzip' not in accept_encoding.lower():
            return response

        # Check content type
        content_type = response.headers.get('Content-Type', '').split(';')[0]
        if content_type not in self.compressible_types:
            return response

        # Check content size
        content = response.data
        if isinstance(content, str):
            content = content.encode('utf-8')

        if len(content) < self.min_size:
            return response

        # Compress content
        try:
            import gzip
            compressed_content = gzip.compress(content, compresslevel=self.compression_level)

            # Update response
            response.data = compressed_content
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Content-Length'] = str(len(compressed_content))
            response.headers['Vary'] = 'Accept-Encoding'

        except Exception as e:
            print(f"Compression error: {e}")

        return response


class CachingMiddleware(BaseMiddleware):
    """
    Middleware for response caching with configurable strategies.
    """

    def __init__(self, cache_ttl: int = 300, cache_size: int = 1000, **kwargs):
        super().__init__(**kwargs)
        self.cache_ttl = cache_ttl
        self.cache_size = cache_size
        self.cache = {}
        self.cache_times = {}
        self.cacheable_methods = {'GET', 'HEAD'}

    def process_request(self, request: Request) -> Optional[Response]:
        """Check cache for existing response."""
        if request.method not in self.cacheable_methods:
            return None

        cache_key = self._generate_cache_key(request)

        # Check if cached response exists and is still valid
        if cache_key in self.cache:
            cached_time = self.cache_times.get(cache_key, 0)
            if time.time() - cached_time < self.cache_ttl:
                return self.cache[cache_key]
            else:
                # Remove expired cache entry
                del self.cache[cache_key]
                del self.cache_times[cache_key]

        return None

    def process_response(self, request: Request, response: Response) -> Optional[Response]:
        """Cache response if appropriate."""
        if request.method not in self.cacheable_methods:
            return response

        # Only cache successful responses
        if response.status != 200:
            return response

        cache_key = self._generate_cache_key(request)

        # Enforce cache size limit
        if len(self.cache) >= self.cache_size:
            self._evict_oldest_entry()

        # Cache the response
        self.cache[cache_key] = response
        self.cache_times[cache_key] = time.time()

        # Add cache headers
        response.headers['Cache-Control'] = f'max-age={self.cache_ttl}'

        return response

    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key for request."""
        return f"{request.method}:{request.path}:{request.query_string}"

    def _evict_oldest_entry(self):
        """Remove oldest cache entry."""
        if self.cache_times:
            oldest_key = min(self.cache_times.keys(), key=lambda k: self.cache_times[k])
            del self.cache[oldest_key]
            del self.cache_times[oldest_key]
