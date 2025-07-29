"""
WolfPy Router Module.

This module provides enhanced URL routing functionality for the WolfPy framework.
It handles route registration, pattern matching, parameter extraction, and includes
advanced features like route caching, trie-based matching, and performance optimization.
"""

import re
import time
import hashlib
import asyncio
import threading
import weakref
from typing import Dict, List, Tuple, Callable, Optional, Any, Union, Pattern, Set
from functools import wraps, lru_cache
from urllib.parse import quote, unquote
from collections import OrderedDict, defaultdict
from concurrent.futures import ThreadPoolExecutor
import json
import gzip


class MatchResult:
    """Result of route matching."""

    def __init__(self, handler: Callable, params: Dict[str, Any], route: 'Route' = None):
        self.handler = handler
        self.params = params
        self.route = route


class TrieNode:
    """Node in the route trie for ultra-fast prefix matching."""

    def __init__(self):
        self.children = {}
        self.routes = []  # Routes that end at this node
        self.is_parameter = False
        self.parameter_name = None
        self.parameter_type = 'str'

    def add_route(self, route: 'Route'):
        """Add a route to this node."""
        self.routes.append(route)

    def get_routes(self, method: str = None):
        """Get routes for a specific method or all routes."""
        if method:
            return [r for r in self.routes if method.upper() in r.methods]
        return self.routes


class RouteTrie:
    """
    Trie data structure for ultra-fast route matching.

    This provides O(k) lookup time where k is the length of the path,
    significantly faster than linear route scanning for large numbers of routes.
    """

    def __init__(self):
        self.root = TrieNode()
        self._route_count = 0

    def add_route(self, route: 'Route'):
        """
        Add a route to the trie.

        Args:
            route: Route object to add
        """
        path_parts = self._split_path(route.pattern)
        current = self.root

        for part in path_parts:
            if part.startswith('<') and part.endswith('>'):
                # Parameter node
                param_key = f"<{part[1:-1]}>"
                if param_key not in current.children:
                    node = TrieNode()
                    node.is_parameter = True
                    # Extract parameter name and type
                    param_content = part[1:-1]
                    if ':' in param_content:
                        param_type, param_name = param_content.split(':', 1)
                    else:
                        param_type, param_name = 'str', param_content
                    node.parameter_name = param_name
                    node.parameter_type = param_type
                    current.children[param_key] = node
                current = current.children[param_key]
            else:
                # Static node
                if part not in current.children:
                    current.children[part] = TrieNode()
                current = current.children[part]

        current.add_route(route)
        self._route_count += 1

    def find_routes(self, path: str, method: str = None):
        """
        Find all routes that match the given path.

        Args:
            path: URL path to match
            method: HTTP method filter

        Returns:
            List of (route, parameters) tuples
        """
        path_parts = self._split_path(path)
        matches = []

        def _search(node: TrieNode, parts: List[str], params: Dict[str, Any], index: int):
            if index == len(parts):
                # End of path, check for routes
                for route in node.get_routes(method):
                    matches.append((route, params.copy()))
                return

            current_part = parts[index]

            # Try exact match first
            if current_part in node.children:
                _search(node.children[current_part], parts, params, index + 1)

            # Try parameter matches
            for key, child in node.children.items():
                if child.is_parameter:
                    # Validate parameter type
                    if self._validate_parameter_type(current_part, child.parameter_type):
                        new_params = params.copy()
                        new_params[child.parameter_name] = self._convert_parameter(
                            current_part, child.parameter_type
                        )
                        _search(child, parts, new_params, index + 1)

        _search(self.root, path_parts, {}, 0)
        return matches

    def _split_path(self, path: str) -> List[str]:
        """Split path into parts, handling empty parts."""
        if path == '/':
            return []
        return [part for part in path.split('/') if part]

    def _validate_parameter_type(self, value: str, param_type: str) -> bool:
        """Validate if value matches parameter type."""
        if param_type == 'int':
            return value.isdigit()
        elif param_type == 'float':
            try:
                float(value)
                return True
            except ValueError:
                return False
        elif param_type == 'uuid':
            import re
            uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
            return bool(re.match(uuid_pattern, value, re.IGNORECASE))
        return True  # str and path types accept anything

    def _convert_parameter(self, value: str, param_type: str):
        """Convert parameter value to appropriate type."""
        if param_type == 'int':
            return int(value)
        elif param_type == 'float':
            return float(value)
        return value  # str, path, uuid stay as strings

    def get_stats(self) -> Dict[str, Any]:
        """Get trie statistics."""
        return {
            'route_count': self._route_count,
            'node_count': self._count_nodes(self.root),
            'max_depth': self._max_depth(self.root),
            'memory_usage_estimate': self._route_count * 200  # Rough estimate
        }

    def _count_nodes(self, node: TrieNode) -> int:
        """Count total nodes in trie."""
        count = 1
        for child in node.children.values():
            count += self._count_nodes(child)
        return count

    def _max_depth(self, node: TrieNode, depth: int = 0) -> int:
        """Calculate maximum depth of trie."""
        if not node.children:
            return depth
        return max(self._max_depth(child, depth + 1) for child in node.children.values())


class RouteConstraint:
    """
    Route constraint for advanced parameter validation.
    """

    def __init__(self, pattern: str = None, validator: Callable = None,
                 converter: Callable = None):
        """
        Initialize route constraint.

        Args:
            pattern: Regex pattern for validation
            validator: Custom validation function
            converter: Function to convert matched value
        """
        self.pattern = re.compile(pattern) if pattern else None
        self.validator = validator
        self.converter = converter or (lambda x: x)

    def validate(self, value: str) -> Tuple[bool, Any]:
        """
        Validate and convert a parameter value.

        Args:
            value: Parameter value to validate

        Returns:
            Tuple of (is_valid, converted_value)
        """
        # Pattern validation
        if self.pattern and not self.pattern.match(value):
            return False, value

        # Custom validator
        if self.validator and not self.validator(value):
            return False, value

        # Convert value
        try:
            converted = self.converter(value)
            return True, converted
        except (ValueError, TypeError):
            return False, value


class RouteVersion:
    """
    Route versioning support for API evolution.
    """

    def __init__(self, version: str, deprecated: bool = False,
                 sunset_date: str = None):
        """
        Initialize route version.

        Args:
            version: Version string (e.g., 'v1', '2.0', '2023-01-01')
            deprecated: Whether this version is deprecated
            sunset_date: ISO date when version will be removed
        """
        self.version = version
        self.deprecated = deprecated
        self.sunset_date = sunset_date

    def get_headers(self) -> Dict[str, str]:
        """Get version-related headers."""
        headers = {'API-Version': self.version}

        if self.deprecated:
            headers['Deprecation'] = 'true'
            if self.sunset_date:
                headers['Sunset'] = self.sunset_date

        return headers


class RouteGroup:
    """
    Route group for organizing related routes with shared middleware and prefixes.
    """

    def __init__(self, prefix: str = '', middleware: List[Callable] = None, name: str = ''):
        """
        Initialize route group.

        Args:
            prefix: URL prefix for all routes in this group
            middleware: List of middleware functions to apply to all routes
            name: Optional name for the route group
        """
        self.prefix = prefix.rstrip('/')
        self.middleware = middleware or []
        self.name = name
        self.routes = []

    def add_route(self, pattern: str, handler: Callable, methods: List[str] = None,
                  middleware: List[Callable] = None, name: str = '', cache_ttl: int = 0):
        """
        Add a route to this group.

        Args:
            pattern: URL pattern (will be prefixed with group prefix)
            handler: Route handler function
            methods: HTTP methods
            middleware: Additional middleware for this specific route
            name: Optional name for the route
            cache_ttl: Cache TTL in seconds
        """
        if methods is None:
            methods = ['GET']

        # Combine group prefix with route pattern
        full_pattern = self.prefix + pattern

        # Combine group middleware with route-specific middleware
        combined_middleware = self.middleware.copy()
        if middleware:
            combined_middleware.extend(middleware)

        route = Route(full_pattern, handler, methods, combined_middleware, name, cache_ttl)
        self.routes.append(route)
        return route


class Route:
    """Represents a single route in the application."""
    
    def __init__(self, pattern: str, handler: Callable, methods: List[str],
                 middleware: List[Callable] = None, name: str = '', cache_ttl: int = 0,
                 constraints: Dict[str, RouteConstraint] = None, version: RouteVersion = None,
                 subdomain: str = None, host: str = None):
        """
        Initialize a route with advanced features.

        Args:
            pattern: URL pattern (can include parameters like /user/<id>)
            handler: Function to handle the route
            methods: List of allowed HTTP methods
            middleware: List of middleware functions for this route
            name: Optional name for the route (for URL generation)
            cache_ttl: Cache TTL in seconds (0 = no caching)
            constraints: Parameter constraints for validation
            version: API version information
            subdomain: Required subdomain (e.g., 'api')
            host: Required host pattern
        """
        self.pattern = pattern
        self.handler = handler
        self.methods = [method.upper() for method in methods]
        self.middleware = middleware or []
        self.name = name
        self.cache_ttl = cache_ttl
        self.constraints = constraints or {}
        self.version = version
        self.subdomain = subdomain
        self.host = host

        # Compile pattern and extract parameters
        self.regex, self.param_names = self._compile_pattern(pattern)

        # Performance tracking
        self._match_cache = {}
        self._cache_hits = 0
        self._cache_misses = 0
        self._last_accessed = time.time()
        self._request_count = 0
        self._total_response_time = 0.0

    @property
    def path(self) -> str:
        """Get the route path (alias for pattern)."""
        return self.pattern

    @property
    def method(self) -> str:
        """Get the primary method (first method in the list)."""
        return self.methods[0] if self.methods else 'GET'
    
    def _compile_pattern(self, pattern: str) -> Tuple[re.Pattern, List[str]]:
        """
        Compile a URL pattern into a regex and extract parameter names.
        
        Args:
            pattern: URL pattern like '/user/<id>' or '/post/<int:id>'
            
        Returns:
            Tuple of (compiled regex, list of parameter names)
        """
        param_names = []
        regex_pattern = pattern
        
        # Find all parameters in the pattern
        param_regex = r'<(?:(\w+):)?(\w+)>'
        
        def replace_param(match):
            param_type = match.group(1) or 'str'
            param_name = match.group(2)
            param_names.append(param_name)
            
            # Define type patterns
            type_patterns = {
                'str': r'([^/]+)',
                'int': r'(\d+)',
                'float': r'(\d+\.?\d*)',
                'path': r'(.+)',
                'uuid': r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'
            }
            
            return type_patterns.get(param_type, r'([^/]+)')
        
        regex_pattern = re.sub(param_regex, replace_param, regex_pattern)
        
        # Escape special regex characters except our parameter patterns
        regex_pattern = '^' + regex_pattern + '$'
        
        return re.compile(regex_pattern), param_names
    
    def match(self, path: str, method: str, request_info: Dict[str, Any] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if this route matches the given path, method, and request info.

        Args:
            path: URL path to match
            method: HTTP method
            request_info: Additional request information (host, subdomain, etc.)

        Returns:
            Tuple of (matches, parameters dict)
        """
        request_info = request_info or {}

        if method.upper() not in self.methods:
            return False, {}

        # Check subdomain constraint
        if self.subdomain:
            request_subdomain = request_info.get('subdomain', '')
            if request_subdomain != self.subdomain:
                return False, {}

        # Check host constraint
        if self.host:
            request_host = request_info.get('host', '')
            if not re.match(self.host, request_host):
                return False, {}

        match = self.regex.match(path)
        if not match:
            return False, {}

        # Extract parameters
        params = {}
        for i, param_name in enumerate(self.param_names):
            value = match.group(i + 1)

            # Apply constraints if defined
            if param_name in self.constraints:
                is_valid, converted_value = self.constraints[param_name].validate(value)
                if not is_valid:
                    return False, {}
                value = converted_value
            else:
                # Try to convert to appropriate type based on the original pattern
                if value.isdigit():
                    value = int(value)
                elif '.' in value and value.replace('.', '').isdigit():
                    value = float(value)
                # else keep as string

            params[param_name] = value

        # Update performance metrics
        self._request_count += 1
        self._last_accessed = time.time()

        return True, params


class Router:
    """
    Advanced URL Router for FoxPy applications.

    Handles route registration, URL pattern matching, parameter extraction,
    route groups, middleware, and performance optimization.
    """

    def __init__(self):
        """Initialize the router."""
        self.routes: List[Route] = []
        self.static_routes: Dict[str, Route] = {}  # For exact matches (optimization)
        self.route_groups: List[RouteGroup] = []
        self.named_routes: Dict[str, Route] = {}  # For URL generation by name

        # Performance tracking
        self._route_stats = {}
        self._total_requests = 0
        self._cache_enabled = True

        # Enhanced caching and optimization
        self._route_cache: Dict[str, tuple] = {}  # Cache for matched routes
        self._cache_hits = 0
        self._cache_misses = 0
        self._max_cache_size = 1000

        # Route tree for faster matching (prefix tree)
        self._route_tree = {}
        self._compiled_routes = []  # Pre-compiled route patterns

        # Advanced routing features
        self._route_trie = RouteTrie()  # Trie for ultra-fast prefix matching
        self._regex_cache = {}  # Cache for compiled regex patterns
        self._route_groups_cache = {}  # Cache for route groups

        # HTTP/2 and modern features preparation
        self._http2_push_resources = {}  # Server push resources
        self._route_priorities = {}  # Route priority mapping
        self._route_weights = {}  # Load balancing weights

        # Advanced performance metrics
        self._detailed_stats = {
            'route_compilation_time': 0.0,
            'trie_lookup_time': 0.0,
            'regex_match_time': 0.0,
            'cache_memory_usage': 0,
            'route_complexity_scores': {}
        }

        # Async routing support
        self._async_executor = ThreadPoolExecutor(max_workers=4)
        self._async_routes = set()

        # Route optimization
        self._route_frequency = defaultdict(int)
        self._optimization_enabled = True
        self._last_optimization = time.time()

        # Advanced caching
        self._route_result_cache = OrderedDict()
        self._cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'memory_usage': 0
        }

        # HTTP/2 Server Push support
        self._push_promises = {}
        self._critical_resources = set()

        # Route health monitoring
        self._route_health = {}
        self._error_thresholds = {}

        # Thread safety
        self._lock = threading.RLock()
    
    def add_route(self, pattern: str, handler: Callable, methods: List[str] = None,
                  middleware: List[Callable] = None, name: str = '', cache_ttl: int = 0,
                  constraints: Dict[str, RouteConstraint] = None, version: RouteVersion = None,
                  subdomain: str = None, host: str = None):
        """
        Add a route to the router with advanced features.

        Args:
            pattern: URL pattern
            handler: Function to handle requests to this route
            methods: List of allowed HTTP methods (default: ['GET'])
            middleware: List of middleware functions for this route
            name: Optional name for the route (for URL generation)
            cache_ttl: Cache TTL in seconds (0 = no caching)
            constraints: Parameter constraints for validation
            version: API version information
            subdomain: Required subdomain (e.g., 'api')
            host: Required host pattern
        """
        if methods is None:
            methods = ['GET']

        route = Route(pattern, handler, methods, middleware, name, cache_ttl,
                     constraints, version, subdomain, host)

        # Add to named routes if name is provided
        if name:
            self.named_routes[name] = route

        # If it's a static route (no parameters), add to static_routes for faster lookup
        if '<' not in pattern:
            for method in route.methods:
                key = f"{method}:{pattern}"
                self.static_routes[key] = route

        self.routes.append(route)

        # Add to trie for fast lookup
        self._route_trie.add_route(route)

        # Calculate route complexity score
        complexity = self._calculate_route_complexity(route)
        self._detailed_stats['route_complexity_scores'][pattern] = complexity

        return route

    def group(self, prefix: str = '', middleware: List[Callable] = None, name: str = '') -> RouteGroup:
        """
        Create a route group with shared prefix and middleware.

        Args:
            prefix: URL prefix for all routes in this group
            middleware: List of middleware functions to apply to all routes
            name: Optional name for the route group

        Returns:
            RouteGroup instance
        """
        group = RouteGroup(prefix, middleware, name)
        self.route_groups.append(group)
        return group

    def register_group(self, group: RouteGroup):
        """
        Register all routes from a route group.

        Args:
            group: RouteGroup to register
        """
        for route in group.routes:
            # Add to named routes if route has a name
            if route.name:
                self.named_routes[route.name] = route

            # Add to static routes for optimization
            if '<' not in route.pattern:
                for method in route.methods:
                    key = f"{method}:{route.pattern}"
                    self.static_routes[key] = route

            self.routes.append(route)
    
    def match(self, path: str, method: str, request_info: Dict[str, Any] = None) -> Optional[MatchResult]:
        """
        Find a matching route for the given path, method, and request info.

        Args:
            path: URL path (without query string)
            method: HTTP method
            request_info: Additional request information (host, subdomain, etc.)

        Returns:
            MatchResult object if match found, None otherwise
        """
        method = method.upper()
        request_info = request_info or {}

        # Strip query string from path if present
        if '?' in path:
            path = path.split('?')[0]

        # Normalize path (remove trailing slash except for root)
        if path != '/' and path.endswith('/'):
            path = path.rstrip('/')

        # Update total request count
        self._total_requests += 1

        # Check cache first
        cache_key = f"{path}:{method}"
        if self._cache_enabled and cache_key in self._route_cache:
            self._cache_hits += 1
            cached_handler, cached_params, cached_route = self._route_cache[cache_key]

            # Update route statistics
            if cached_route:
                route_key = f"{cached_route.pattern}:{method}"
                if route_key in self._route_stats:
                    self._route_stats[route_key]['hits'] += 1
                    self._route_stats[route_key]['last_accessed'] = time.time()

            if cached_handler is not None:
                return MatchResult(cached_handler, cached_params, cached_route)
            else:
                return None

        self._cache_misses += 1

        # First, try static routes for faster lookup (if no special constraints)
        static_key = f"{method}:{path}"
        if static_key in self.static_routes:
            route = self.static_routes[static_key]
            # Check if route has constraints that need validation
            if not route.subdomain and not route.host:
                result = MatchResult(route.handler, {}, route)
                self._cache_route_result(cache_key, route.handler, {}, route)
                return result

        # Then try dynamic routes
        for route in self.routes:
            matches, params = route.match(path, method, request_info)
            if matches:
                # Update route statistics
                route_key = f"{route.pattern}:{method}"
                if route_key not in self._route_stats:
                    self._route_stats[route_key] = {
                        'hits': 0,
                        'avg_response_time': 0.0,
                        'last_accessed': time.time()
                    }
                self._route_stats[route_key]['hits'] += 1
                self._route_stats[route_key]['last_accessed'] = time.time()

                # Cache the result
                self._cache_route_result(cache_key, route.handler, params, route)
                return MatchResult(route.handler, params, route)

        # Try trie-based matching for better performance
        trie_start = time.time()
        trie_matches = self._route_trie.find_routes(path, method)
        self._detailed_stats['trie_lookup_time'] += time.time() - trie_start

        if trie_matches:
            # Use the first match (routes are added in order)
            route, params = trie_matches[0]

            # Validate with full route matching (for constraints, etc.)
            matches, validated_params = route.match(path, method, request_info)
            if matches:
                # Update route statistics
                route_key = f"{route.pattern}:{method}"
                if route_key not in self._route_stats:
                    self._route_stats[route_key] = {
                        'hits': 0,
                        'avg_response_time': 0.0,
                        'last_accessed': time.time()
                    }
                self._route_stats[route_key]['hits'] += 1
                self._route_stats[route_key]['last_accessed'] = time.time()

                # Cache the result
                self._cache_route_result(cache_key, route.handler, validated_params, route)
                return MatchResult(route.handler, validated_params, route)

        # Cache negative result
        self._cache_route_result(cache_key, None, {}, None)
        return None

    def match_with_route(self, path: str, method: str, request_info: Dict[str, Any] = None) -> Tuple[Optional[Callable], Dict[str, Any], Optional[Route]]:
        """
        Find a matching route and return the route object as well.

        Args:
            path: URL path (without query string)
            method: HTTP method
            request_info: Additional request information (host, subdomain, etc.)

        Returns:
            Tuple of (handler function, parameters dict, route) or (None, {}, None) if no match
        """
        method = method.upper()
        request_info = request_info or {}

        # Strip query string from path if present
        if '?' in path:
            path = path.split('?')[0]

        # Normalize path (remove trailing slash except for root)
        if path != '/' and path.endswith('/'):
            path = path.rstrip('/')

        # Update total request count
        self._total_requests += 1

        # First, try static routes for faster lookup (if no special constraints)
        static_key = f"{method}:{path}"
        if static_key in self.static_routes:
            route = self.static_routes[static_key]
            # Check if route has constraints that need validation
            if not route.subdomain and not route.host:
                return route.handler, {}, route

        # Then try dynamic routes
        for route in self.routes:
            matches, params = route.match(path, method, request_info)
            if matches:
                # Update route statistics
                route_key = f"{route.pattern}:{method}"
                if route_key not in self._route_stats:
                    self._route_stats[route_key] = {
                        'hits': 0,
                        'avg_response_time': 0.0,
                        'last_accessed': time.time()
                    }
                self._route_stats[route_key]['hits'] += 1
                self._route_stats[route_key]['last_accessed'] = time.time()

                return route.handler, params, route

        return None, {}, None

    def get_routes(self) -> List[Route]:
        """Get all registered routes."""
        return self.routes.copy()

    def optimize_routes(self):
        """
        Optimize route ordering based on access frequency and complexity.
        """
        if not self._optimization_enabled:
            return

        with self._lock:
            # Sort routes by frequency (most accessed first)
            route_scores = []
            for route in self.routes:
                frequency = self._route_frequency.get(route.pattern, 0)
                complexity = self._calculate_route_complexity(route)
                score = frequency / (complexity + 1)  # Higher frequency, lower complexity = higher score
                route_scores.append((score, route))

            # Re-order routes by score (highest first)
            route_scores.sort(key=lambda x: x[0], reverse=True)
            self.routes = [route for _, route in route_scores]

            # Update trie with optimized order
            self._route_trie = RouteTrie()
            for route in self.routes:
                self._route_trie.add_route(route)

            self._last_optimization = time.time()

    def _calculate_route_complexity(self, route: Route) -> int:
        """Calculate complexity score for a route."""
        complexity = 0

        # Parameter complexity
        complexity += len(route.param_names) * 2

        # Constraint complexity
        complexity += len(route.constraints) * 3

        # Middleware complexity
        complexity += len(route.middleware)

        # Pattern complexity (regex special chars)
        special_chars = sum(1 for c in route.pattern if c in r'.*+?^${}[]|()\/')
        complexity += special_chars

        return complexity

    def add_server_push_resource(self, route_pattern: str, resource_path: str,
                                resource_type: str = 'script'):
        """
        Add HTTP/2 server push resource for a route.

        Args:
            route_pattern: Route pattern to associate with
            resource_path: Path to resource to push
            resource_type: Type of resource (script, style, image, etc.)
        """
        if route_pattern not in self._push_promises:
            self._push_promises[route_pattern] = []

        self._push_promises[route_pattern].append({
            'path': resource_path,
            'type': resource_type,
            'priority': 'high' if resource_type in ['script', 'style'] else 'low'
        })

    def get_push_resources(self, route_pattern: str) -> List[Dict[str, str]]:
        """Get server push resources for a route."""
        return self._push_promises.get(route_pattern, [])

    def set_route_priority(self, pattern: str, priority: int):
        """
        Set priority for a route (higher priority routes are checked first).

        Args:
            pattern: Route pattern
            priority: Priority value (higher = more priority)
        """
        self._route_priorities[pattern] = priority

        # Re-sort routes by priority
        def route_priority(route):
            return self._route_priorities.get(route.pattern, 0)

        self.routes.sort(key=route_priority, reverse=True)

    def enable_route_health_monitoring(self, pattern: str, error_threshold: float = 0.1):
        """
        Enable health monitoring for a route.

        Args:
            pattern: Route pattern to monitor
            error_threshold: Error rate threshold (0.0-1.0)
        """
        self._route_health[pattern] = {
            'total_requests': 0,
            'error_count': 0,
            'last_error': None,
            'status': 'healthy'
        }
        self._error_thresholds[pattern] = error_threshold

    def record_route_result(self, pattern: str, success: bool, error: Exception = None):
        """
        Record the result of a route execution for health monitoring.

        Args:
            pattern: Route pattern
            success: Whether the route executed successfully
            error: Exception if route failed
        """
        if pattern not in self._route_health:
            return

        health = self._route_health[pattern]
        health['total_requests'] += 1

        if not success:
            health['error_count'] += 1
            health['last_error'] = str(error) if error else 'Unknown error'

            # Check if error rate exceeds threshold
            error_rate = health['error_count'] / health['total_requests']
            threshold = self._error_thresholds.get(pattern, 0.1)

            if error_rate > threshold:
                health['status'] = 'unhealthy'
            else:
                health['status'] = 'degraded'
        else:
            # Reset status if we have enough successful requests
            if health['total_requests'] > 10:
                error_rate = health['error_count'] / health['total_requests']
                threshold = self._error_thresholds.get(pattern, 0.1)

                if error_rate <= threshold / 2:  # Half the threshold for recovery
                    health['status'] = 'healthy'

    def get_route_health(self, pattern: str = None) -> Dict[str, Any]:
        """
        Get health status for routes.

        Args:
            pattern: Specific route pattern, or None for all routes

        Returns:
            Health status information
        """
        if pattern:
            return self._route_health.get(pattern, {})
        return self._route_health.copy()

    def _cache_route_result(self, cache_key: str, handler: Callable,
                           params: Dict[str, Any], route: Route):
        """Cache a route matching result."""
        if not self._cache_enabled:
            return

        # Implement LRU eviction
        if len(self._route_result_cache) >= self._max_cache_size:
            # Remove oldest entry
            oldest_key = next(iter(self._route_result_cache))
            del self._route_result_cache[oldest_key]
            self._cache_stats['evictions'] += 1

        self._route_result_cache[cache_key] = (handler, params, route, time.time())

        # Update cache memory usage estimate
        self._cache_stats['memory_usage'] = len(self._route_result_cache) * 200  # Rough estimate

    def _get_cached_route_result(self, cache_key: str) -> Optional[Tuple[Callable, Dict[str, Any], Route]]:
        """Get cached route result if available."""
        if not self._cache_enabled or cache_key not in self._route_result_cache:
            self._cache_stats['misses'] += 1
            return None

        handler, params, route, timestamp = self._route_result_cache[cache_key]

        # Move to end (LRU)
        del self._route_result_cache[cache_key]
        self._route_result_cache[cache_key] = (handler, params, route, timestamp)

        self._cache_stats['hits'] += 1
        return handler, params, route

    def find_matching_routes(self, path: str) -> List[Route]:
        """
        Find all routes that match the given path (regardless of method).

        Args:
            path: URL path

        Returns:
            List of matching routes
        """
        # Strip query string from path if present
        if '?' in path:
            path = path.split('?')[0]

        # Normalize path
        if path != '/' and path.endswith('/'):
            path = path.rstrip('/')

        matching_routes = []
        for route in self.routes:
            match = route.regex.match(path)
            if match:
                matching_routes.append(route)

        return matching_routes

    def get_allowed_methods(self, path: str) -> List[str]:
        """
        Get all allowed HTTP methods for a given path.

        Args:
            path: URL path

        Returns:
            List of allowed HTTP methods
        """
        matching_routes = self.find_matching_routes(path)
        methods = set()
        for route in matching_routes:
            methods.update(route.methods)
        return sorted(list(methods))

    def url_for(self, name_or_handler: Union[str, Callable], **params) -> Optional[str]:
        """
        Generate URL for a given route name or handler function.

        Args:
            name_or_handler: Route name (string) or handler function
            **params: Parameters to substitute in the URL pattern

        Returns:
            Generated URL or None if route not found
        """
        route = None

        # Try to find route by name first
        if isinstance(name_or_handler, str):
            route = self.named_routes.get(name_or_handler)
        else:
            # Find by handler function
            for r in self.routes:
                if r.handler == name_or_handler:
                    route = r
                    break

        if not route:
            return None

        url = route.pattern

        # Substitute parameters
        for param_name, param_value in params.items():
            # Handle both simple and typed parameters
            patterns = [
                f'<{param_name}>',
                f'<str:{param_name}>',
                f'<int:{param_name}>',
                f'<float:{param_name}>',
                f'<path:{param_name}>',
                f'<uuid:{param_name}>'
            ]

            for pattern in patterns:
                if pattern in url:
                    url = url.replace(pattern, str(param_value))
                    break

        return url

    def get_route_stats(self) -> Dict[str, Any]:
        """
        Get routing performance statistics.

        Returns:
            Dictionary with routing statistics
        """
        return {
            'total_routes': len(self.routes),
            'static_routes': len(self.static_routes),
            'named_routes': len(self.named_routes),
            'route_groups': len(self.route_groups),
            'total_requests': self._total_requests,
            'cache_enabled': self._cache_enabled,
            'route_stats': self._route_stats.copy()
        }

    def _cache_route_result(self, cache_key: str, handler: Optional[Callable],
                           params: Dict[str, Any], route: Optional[Route]):
        """
        Cache a route matching result.

        Args:
            cache_key: Cache key for the route
            handler: Route handler function
            params: Route parameters
            route: Route object
        """
        if not self._cache_enabled:
            return

        # Implement LRU cache by removing oldest entries when cache is full
        if len(self._route_cache) >= self._max_cache_size:
            # Remove 10% of oldest entries
            items_to_remove = max(1, self._max_cache_size // 10)
            oldest_keys = list(self._route_cache.keys())[:items_to_remove]
            for key in oldest_keys:
                del self._route_cache[key]

        self._route_cache[cache_key] = (handler, params, route)

    def _calculate_route_complexity(self, route: Route) -> float:
        """
        Calculate complexity score for a route.

        Args:
            route: Route to analyze

        Returns:
            Complexity score (higher = more complex)
        """
        score = 0.0

        # Base complexity from pattern
        score += len(route.pattern.split('/'))

        # Parameter complexity
        param_count = len(route.param_names)
        score += param_count * 2

        # Constraint complexity
        score += len(route.constraints) * 3

        # Middleware complexity
        score += len(route.middleware) * 1.5

        # Method complexity (more methods = more complex)
        score += len(route.methods) * 0.5

        # Special features
        if route.subdomain:
            score += 2
        if route.host:
            score += 2
        if route.version:
            score += 1

        return score

    def add_http2_push_resource(self, route_pattern: str, resource_path: str,
                               resource_type: str = 'script'):
        """
        Add HTTP/2 server push resource for a route.

        Args:
            route_pattern: Route pattern to push resources for
            resource_path: Path to resource to push
            resource_type: Type of resource (script, style, image, etc.)
        """
        if route_pattern not in self._http2_push_resources:
            self._http2_push_resources[route_pattern] = []

        self._http2_push_resources[route_pattern].append({
            'path': resource_path,
            'type': resource_type
        })

    def get_push_resources(self, route_pattern: str) -> List[Dict[str, str]]:
        """Get HTTP/2 push resources for a route pattern."""
        return self._http2_push_resources.get(route_pattern, [])

    def set_route_priority(self, route_pattern: str, priority: int):
        """
        Set priority for a route (higher priority routes are checked first).

        Args:
            route_pattern: Route pattern
            priority: Priority value (higher = checked first)
        """
        self._route_priorities[route_pattern] = priority
        # Re-sort routes by priority
        self._sort_routes_by_priority()

    def _sort_routes_by_priority(self):
        """Sort routes by priority (highest first)."""
        def get_priority(route):
            return self._route_priorities.get(route.pattern, 0)

        self.routes.sort(key=get_priority, reverse=True)

    def optimize_routes(self):
        """
        Optimize route order based on usage statistics and complexity.

        This method reorders routes to put frequently used, simple routes first.
        """
        def route_score(route):
            # Get usage statistics
            route_key = f"{route.pattern}:{','.join(route.methods)}"
            hits = self._route_stats.get(route_key, {}).get('hits', 0)

            # Get complexity score
            complexity = self._detailed_stats['route_complexity_scores'].get(route.pattern, 1.0)

            # Higher hits and lower complexity = higher score (checked first)
            return hits / complexity if complexity > 0 else hits

        self.routes.sort(key=route_score, reverse=True)

    def get_advanced_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive router statistics including advanced metrics.

        Returns:
            Dictionary with detailed statistics
        """
        basic_stats = self.get_cache_stats()
        trie_stats = self._route_trie.get_stats()

        return {
            **basic_stats,
            'trie_stats': trie_stats,
            'detailed_performance': self._detailed_stats,
            'route_count': len(self.routes),
            'static_route_count': len(self.static_routes),
            'named_route_count': len(self.named_routes),
            'route_group_count': len(self.route_groups),
            'http2_push_resources': len(self._http2_push_resources),
            'route_priorities': len(self._route_priorities),
            'total_requests': self._total_requests,
            'average_complexity': sum(self._detailed_stats['route_complexity_scores'].values()) /
                                max(len(self._detailed_stats['route_complexity_scores']), 1)
        }

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get route cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0

        return {
            'cache_enabled': self._cache_enabled,
            'cache_size': len(self._route_cache),
            'max_cache_size': self._max_cache_size,
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'hit_rate': f"{hit_rate:.2f}%"
        }

    def clear_cache(self):
        """Clear all route caches."""
        self._route_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0

        for route in self.routes:
            if hasattr(route, '_match_cache'):
                route._match_cache.clear()
                route._cache_hits = 0
                route._cache_misses = 0
