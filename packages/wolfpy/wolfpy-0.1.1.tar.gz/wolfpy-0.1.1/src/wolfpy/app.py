"""
Main WolfPy application class.

This module contains the core WolfPy application class that serves as the main
entry point for creating web applications with the framework.
"""

import os
import sys
import mimetypes
import gzip
import hashlib
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Any, Optional, Union
from wsgiref.simple_server import make_server
from contextlib import contextmanager

from .core.router import Router
from .core.request import Request
from .core.response import Response
from .core.middleware import Middleware
from .core.session import Session
from .core.auth import Auth
from .core.database import Database
from .core.template_engine import TemplateEngine
from .core.performance import PerformanceManager
from .core.cache import CacheManager, MemoryCacheBackend
from .core.api import APIFramework
from .core.error_handling import (
    ExceptionMiddleware, ErrorLogger, ErrorPageManager,
    TracebackFormatter, ValidationErrorHandler
)
from .core.docs import DocumentationSystem
from .core.plugins import PluginManager


class WolfPy:
    """
    Enhanced WolfPy application class.

    This class serves as the central application object that handles:
    - Route registration and management with advanced features
    - WSGI application interface with performance monitoring
    - Middleware processing with dependency management
    - Request/response handling with security features
    - Static file serving with caching and compression
    - Template rendering with asset management
    - Performance monitoring and analytics
    - Enhanced error handling and debugging
    - Security features (CSRF, rate limiting, CORS)
    - Session management with multiple backends
    """

    def __init__(self,
                 debug: bool = False,
                 static_folder: str = "static",
                 template_folder: str = "templates",
                 secret_key: Optional[str] = None,
                 enable_performance_monitoring: bool = True,
                 enable_caching: bool = True,
                 enable_api_framework: bool = True,
                 max_request_size: int = 16 * 1024 * 1024,  # 16MB
                 request_timeout: int = 30,
                 api_prefix: str = "/api",
                 api_version: str = "v1",
                 enable_error_logging: bool = True,
                 log_file: str = None,
                 log_level: str = "INFO",
                 docs_dir: str = "docs",
                 enable_docs: bool = True,
                 enable_plugins: bool = True,
                 enable_admin: bool = False,
                 admin_url: str = "/admin",
                 enable_websockets: bool = False,
                 enable_realtime: bool = False):
        """
        Initialize a new WolfPy application.

        Args:
            debug: Enable debug mode for development
            static_folder: Directory for static files
            template_folder: Directory for templates
            secret_key: Secret key for sessions and security
            enable_performance_monitoring: Enable request performance tracking
            enable_caching: Enable advanced caching system
            enable_api_framework: Enable REST API framework
            max_request_size: Maximum request size in bytes
            request_timeout: Request timeout in seconds
            api_prefix: API URL prefix
            api_version: API version
            enable_error_logging: Enable error logging
            log_file: Path to log file (None for default)
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            docs_dir: Directory containing documentation files
            enable_docs: Enable documentation system at /docs
            enable_plugins: Enable plugin system
            enable_admin: Enable admin dashboard at /admin
            admin_url: URL prefix for admin interface
            enable_websockets: Enable WebSocket support
            enable_realtime: Enable real-time features (rooms, channels)
        """
        self.debug = debug
        self.static_folder = static_folder
        self.template_folder = template_folder
        self.secret_key = secret_key or os.urandom(24).hex()
        self.enable_performance_monitoring = enable_performance_monitoring
        self.enable_caching = enable_caching
        self.enable_api_framework = enable_api_framework
        self.max_request_size = max_request_size
        self.request_timeout = request_timeout
        self.api_prefix = api_prefix
        self.api_version = api_version
        self.enable_error_logging = enable_error_logging
        self.log_file = log_file
        self.log_level = log_level
        self.docs_dir = docs_dir
        self.enable_docs = enable_docs
        self.enable_plugins = enable_plugins
        self.enable_admin = enable_admin
        self.admin_url = admin_url
        self.enable_websockets = enable_websockets
        self.enable_realtime = enable_realtime

        # Core components
        self.router = Router()
        self.middleware = Middleware()
        self.session = Session(secret_key=self.secret_key)
        self.auth = Auth()
        self.database = Database()
        self.template_engine = TemplateEngine(
            template_folders=template_folder,
            cache_enabled=not debug,
            auto_reload=debug
        )

        # Advanced components
        self.performance_manager = PerformanceManager(enabled=enable_performance_monitoring)

        # Caching system
        if enable_caching:
            self.cache_manager = CacheManager(MemoryCacheBackend(max_size=10000))
        else:
            self.cache_manager = None

        # API framework
        if enable_api_framework:
            self.api = APIFramework(self, prefix=api_prefix, version=api_version)
        else:
            self.api = None

        # Error handling system
        if enable_error_logging:
            self.error_logger = ErrorLogger(
                log_level=log_level,
                log_file=log_file or f"wolfpy_{datetime.now().strftime('%Y%m%d')}.log",
                enable_console=debug,
                enable_file=True
            )
        else:
            self.error_logger = None

        self.error_page_manager = ErrorPageManager(
            template_engine=self.template_engine,
            debug_mode=debug
        )

        self.traceback_formatter = TracebackFormatter(
            debug_mode=debug,
            show_locals=debug
        )

        self.exception_middleware = ExceptionMiddleware(
            debug_mode=debug,
            logger=self.error_logger,
            error_page_manager=self.error_page_manager,
            traceback_formatter=self.traceback_formatter
        )

        # Add exception middleware to the middleware stack
        self.middleware.add(self.exception_middleware, priority=1000)  # High priority

        self.validation_error_handler = ValidationErrorHandler()

        # Documentation system
        if enable_docs:
            self.docs = DocumentationSystem(docs_dir=docs_dir)
            self.docs.register_routes(self)
        else:
            self.docs = None

        # Plugin system
        if enable_plugins:
            self.plugin_manager = PluginManager(app=self)
        else:
            self.plugin_manager = None

        # Admin system
        if enable_admin:
            from .core.admin import site as admin_site
            self.admin_site = admin_site
            # Register admin routes
            admin_site.register_routes(self, admin_url)
        else:
            self.admin_site = None

        # ASGI and WebSocket support
        if enable_websockets or enable_realtime:
            from .core.asgi import ASGIApplication
            from .core.websocket import WebSocketManager
            from .core.realtime import RealtimeManager

            self.websocket_manager = WebSocketManager()
            self.asgi_app = ASGIApplication(self)

            if enable_realtime:
                self.realtime_manager = RealtimeManager(self.websocket_manager)
                self.asgi_app.realtime_manager = self.realtime_manager
            else:
                self.realtime_manager = None
        else:
            self.websocket_manager = None
            self.asgi_app = None
            self.realtime_manager = None

        # Application state
        self.before_request_handlers: List[Callable] = []
        self.after_request_handlers: List[Callable] = []
        self.error_handlers: Dict[int, Callable] = {}

        # Performance monitoring
        self._request_stats = {
            'total_requests': 0,
            'total_response_time': 0.0,
            'error_count': 0,
            'status_codes': {},
            'slow_requests': [],  # Requests taking > 1 second
        }
        self._stats_lock = threading.Lock()

        # Request context
        self._request_context = threading.local()
        
    def route(self, path: str, methods: List[str] = None, middleware: List[Callable] = None,
              name: str = '', cache_ttl: int = 0, constraints: Dict = None,
              version = None, subdomain: str = None, host: str = None):
        """
        Decorator for registering routes with advanced features.

        Args:
            path: URL path pattern
            methods: HTTP methods (default: ['GET'])
            middleware: List of middleware functions for this route
            name: Optional name for the route (for URL generation)
            cache_ttl: Cache TTL in seconds (0 = no caching)
            constraints: Parameter constraints for validation
            version: API version information
            subdomain: Required subdomain (e.g., 'api')
            host: Required host pattern

        Returns:
            Decorator function
        """
        if methods is None:
            methods = ['GET']

        def decorator(func: Callable):
            self.router.add_route(
                path, func, methods, middleware, name, cache_ttl,
                constraints, version, subdomain, host
            )
            return func
        return decorator
    
    def before_request(self, func: Callable):
        """Register a function to run before each request."""
        self.before_request_handlers.append(func)
        return func
    
    def after_request(self, func: Callable):
        """Register a function to run after each request."""
        self.after_request_handlers.append(func)
        return func
    
    def error_handler(self, status_code: int):
        """Register an error handler for a specific status code."""
        def decorator(func: Callable):
            self.error_handlers[status_code] = func
            # Also register with error page manager
            self.error_page_manager.register_handler(status_code, func)
            return func
        return decorator

    def register_error_handler(self, status_code: int, handler: Callable):
        """Register an error handler programmatically."""
        self.error_handlers[status_code] = handler
        self.error_page_manager.register_handler(status_code, handler)

    def log_error(self, message: str, exception: Exception = None, request: Request = None):
        """Log an error with context information."""
        if self.error_logger:
            from .core.error_handling import ErrorContext
            context = ErrorContext(
                request=request,
                exception=exception,
                message=message,
                status_code=500 if exception else 400
            )
            self.error_logger.log_error(context)

    def log_validation_error(self, field: str, message: str, value: Any = None, request: Request = None):
        """Log a validation error."""
        if self.error_logger:
            self.error_logger.log_validation_error(field, message, value, request)

    def handle_validation_errors(self, errors: Dict[str, List[str]], format_type: str = 'json') -> Response:
        """Handle validation errors and return appropriate response."""
        self.validation_error_handler.clear()
        self.validation_error_handler.add_errors(errors)

        if format_type == 'html':
            # For HTML responses, you might want to render a form with errors
            return Response(
                self.validation_error_handler.to_html(),
                status=422,
                headers={'Content-Type': 'text/html'}
            )
        else:
            # Default to JSON response
            return self.validation_error_handler.to_response(422)
    
    def add_middleware(self, middleware_func: Callable, priority: int = 0):
        """
        Add middleware to the application.

        Args:
            middleware_func: Middleware function or class
            priority: Priority for ordering (higher runs first)
        """
        self.middleware.add(middleware_func, priority)

    def cache(self, ttl: int = 300, cache_name: str = 'default', key_func: Callable = None):
        """
        Decorator for caching function results.

        Args:
            ttl: Time to live in seconds
            cache_name: Name of cache to use
            key_func: Function to generate cache key
        """
        if self.cache_manager:
            return self.cache_manager.cache_function(ttl, cache_name, key_func)
        else:
            # Return no-op decorator if caching is disabled
            def decorator(func):
                return func
            return decorator

    def websocket(self, path: str):
        """
        Decorator for WebSocket routes.

        Args:
            path: WebSocket path pattern

        Example:
            @app.websocket('/ws')
            async def websocket_handler(websocket):
                await websocket.accept()
                while True:
                    message = await websocket.receive_json()
                    await websocket.send_json({'echo': message})
        """
        def decorator(handler):
            if self.asgi_app:
                self.asgi_app.add_websocket_route(path, handler)
            else:
                raise RuntimeError("WebSocket support not enabled. Set enable_websockets=True")
            return handler
        return decorator

    def async_route(self, path: str, methods: List[str] = None):
        """
        Decorator for async HTTP routes.

        Args:
            path: Route path pattern
            methods: List of HTTP methods

        Example:
            @app.async_route('/api/data')
            async def get_data(request):
                data = await fetch_data_async()
                return {'data': data}
        """
        def decorator(handler):
            if self.asgi_app:
                self.asgi_app.add_async_route(path, handler, methods)
            else:
                raise RuntimeError("Async route support not enabled. Set enable_websockets=True")
            return handler
        return decorator

    def invalidate_cache_group(self, group: str):
        """
        Invalidate all cache entries in a group.

        Args:
            group: Cache group name
        """
        if self.cache_manager:
            self.cache_manager.invalidate_group(group)

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary containing cache metrics
        """
        if self.cache_manager:
            return self.cache_manager.get_all_stats()
        return {}

    def api_endpoint(self, path: str, methods: List[str] = None, **kwargs):
        """
        Decorator for API endpoints.

        Args:
            path: API endpoint path
            methods: HTTP methods
            **kwargs: Additional API endpoint options
        """
        if self.api:
            return self.api.endpoint(path, methods, **kwargs)
        else:
            # Fallback to regular route if API framework is disabled
            return self.route(f"{self.api_prefix}/{self.api_version}{path}", methods)

    @contextmanager
    def request_context(self, request: Request):
        """
        Context manager for request-scoped data.

        Args:
            request: Current request object
        """
        self._request_context.request = request
        self._request_context.start_time = time.time()
        try:
            yield
        finally:
            if hasattr(self._request_context, 'request'):
                delattr(self._request_context, 'request')
            if hasattr(self._request_context, 'start_time'):
                delattr(self._request_context, 'start_time')

    def get_current_request(self) -> Optional[Request]:
        """Get the current request from thread-local storage."""
        return getattr(self._request_context, 'request', None)

    def record_request_stats(self, status_code: int, response_time: float):
        """
        Record request statistics for performance monitoring.

        Args:
            status_code: HTTP status code
            response_time: Request processing time in seconds
        """
        if not self.enable_performance_monitoring:
            return

        with self._stats_lock:
            self._request_stats['total_requests'] += 1
            self._request_stats['total_response_time'] += response_time

            # Track status codes
            if status_code not in self._request_stats['status_codes']:
                self._request_stats['status_codes'][status_code] = 0
            self._request_stats['status_codes'][status_code] += 1

            # Track errors
            if status_code >= 400:
                self._request_stats['error_count'] += 1

            # Track slow requests (> 1 second)
            if response_time > 1.0:
                self._request_stats['slow_requests'].append({
                    'timestamp': time.time(),
                    'response_time': response_time,
                    'status_code': status_code
                })
                # Keep only last 100 slow requests
                if len(self._request_stats['slow_requests']) > 100:
                    self._request_stats['slow_requests'] = self._request_stats['slow_requests'][-100:]

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get application performance statistics.

        Returns:
            Dictionary containing performance metrics
        """
        # Use advanced performance manager if available
        if self.performance_manager:
            return self.performance_manager.get_performance_summary()

        # Fallback to basic stats
        with self._stats_lock:
            stats = self._request_stats.copy()

        # Calculate derived metrics
        if stats['total_requests'] > 0:
            stats['avg_response_time'] = stats['total_response_time'] / stats['total_requests']
            stats['error_rate'] = stats['error_count'] / stats['total_requests']
        else:
            stats['avg_response_time'] = 0.0
            stats['error_rate'] = 0.0

        return stats

    def serve_static_file(self, path: str, request_headers: Dict[str, str] = None) -> Response:
        """
        Serve a static file from the static folder with advanced features.

        Args:
            path: Relative path to the static file
            request_headers: Request headers for conditional requests

        Returns:
            Response object with file content, caching headers, and compression
        """
        request_headers = request_headers or {}

        # Security: prevent directory traversal
        if '..' in path or path.startswith('/'):
            return Response("Forbidden", status=403)

        file_path = os.path.join(self.static_folder, path)

        # Check if file exists and is within static folder
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return Response("Not Found", status=404)

        # Verify the file is within the static folder (security)
        static_abs = os.path.abspath(self.static_folder)
        file_abs = os.path.abspath(file_path)
        if not file_abs.startswith(static_abs):
            return Response("Forbidden", status=403)

        try:
            # Get file stats
            file_stat = os.stat(file_path)
            file_size = file_stat.st_size
            last_modified = datetime.fromtimestamp(file_stat.st_mtime)

            # Generate ETag
            etag = hashlib.md5(f"{file_path}{file_stat.st_mtime}{file_size}".encode()).hexdigest()

            # Check conditional requests
            if_none_match = request_headers.get('If-None-Match')
            if_modified_since = request_headers.get('If-Modified-Since')

            # Handle If-None-Match (ETag)
            if if_none_match and if_none_match.strip('"') == etag:
                return Response("", status=304, headers={'ETag': f'"{etag}"'})

            # Handle If-Modified-Since
            if if_modified_since:
                try:
                    if_modified_date = datetime.strptime(if_modified_since, '%a, %d %b %Y %H:%M:%S GMT')
                    if last_modified <= if_modified_date:
                        return Response("", status=304)
                except ValueError:
                    pass

            # Read file content
            with open(file_path, 'rb') as f:
                content = f.read()

            # Guess content type
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                content_type = 'application/octet-stream'

            # Prepare headers
            headers = {
                'Content-Type': content_type,
                'ETag': f'"{etag}"',
                'Last-Modified': last_modified.strftime('%a, %d %b %Y %H:%M:%S GMT'),
                'Content-Length': str(len(content))
            }

            # Add caching headers
            if self._should_cache_static_file(file_path):
                cache_duration = 86400  # 1 day for most files
                if any(file_path.endswith(ext) for ext in ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.ico']):
                    cache_duration = 604800  # 1 week for assets

                expires = datetime.now().replace(tzinfo=None) + timedelta(seconds=cache_duration)
                headers.update({
                    'Cache-Control': f'public, max-age={cache_duration}',
                    'Expires': expires.strftime('%a, %d %b %Y %H:%M:%S GMT')
                })

            # Check if compression is supported and beneficial
            accept_encoding = request_headers.get('Accept-Encoding', '')
            if ('gzip' in accept_encoding and
                self._should_compress_file(file_path, content) and
                len(content) > 1024):  # Only compress files > 1KB

                content = gzip.compress(content)
                headers['Content-Encoding'] = 'gzip'
                headers['Content-Length'] = str(len(content))

            return Response(content, headers=headers)

        except Exception as e:
            if self.debug:
                return Response(f"Static file error: {e}", status=500)
            return Response("Internal Server Error", status=500)

    def _should_cache_static_file(self, file_path: str) -> bool:
        """Check if a static file should be cached."""
        # Cache most static assets
        cacheable_extensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.ico',
                               '.woff', '.woff2', '.ttf', '.eot', '.svg', '.pdf']
        return any(file_path.endswith(ext) for ext in cacheable_extensions)

    def _should_compress_file(self, file_path: str, content: bytes) -> bool:
        """Check if a file should be compressed."""
        # Compress text-based files
        compressible_types = ['.css', '.js', '.html', '.htm', '.txt', '.json', '.xml', '.svg']
        is_compressible_type = any(file_path.endswith(ext) for ext in compressible_types)

        # Also check if content is already compressed
        if len(content) > 2:
            # Check for gzip magic number
            if content[:2] == b'\x1f\x8b':
                return False

        return is_compressible_type
    
    def wsgi_app(self, environ: Dict[str, Any], start_response: Callable):
        """
        Enhanced WSGI application interface with performance monitoring and better error handling.

        Args:
            environ: WSGI environment dictionary
            start_response: WSGI start_response callable

        Returns:
            Response iterator
        """
        start_time = time.time()
        response = None
        request_id = None

        try:
            # Create request object
            request = Request(environ)

            # Start performance tracking
            if self.performance_manager:
                request_id = f"{request.method}_{request.path}_{start_time}_{threading.get_ident()}"
                self.performance_manager.start_request(request_id, request.method, request.path)

            # Check request size limit
            content_length = int(environ.get('CONTENT_LENGTH') or 0)
            if content_length > self.max_request_size:
                response = Response("Request Entity Too Large", status=413)
                return self._finalize_response(response, start_response, start_time)

            # Use request context
            with self.request_context(request):
                # Process middleware (before request)
                middleware_result = self.middleware.process_request(request)
                if isinstance(middleware_result, Response):
                    # Middleware returned a response (e.g., authentication failure)
                    response = middleware_result
                else:
                    if middleware_result is not None:
                        request = middleware_result

                    # Run before request handlers
                    for handler in self.before_request_handlers:
                        try:
                            result = handler(request)
                            if isinstance(result, Response):
                                response = result
                                break
                        except Exception as e:
                            if self.debug:
                                raise
                            print(f"Error in before_request handler: {e}")

                    if response is None:
                        # Check for static files first
                        if request.path.startswith('/static/'):
                            static_path = request.path[8:]  # Remove '/static/' prefix
                            response = self.serve_static_file(static_path, request.headers)
                        else:
                            # Route the request
                            match_result = self.router.match(request.path, request.method)
                            if match_result:
                                handler = match_result.handler
                                params = match_result.params
                            else:
                                handler = None
                                params = {}

                            if handler is None:
                                # Check if path exists with different methods (405 Method Not Allowed)
                                allowed_methods = self.router.get_allowed_methods(request.path)
                                if allowed_methods:
                                    response = Response("Method Not Allowed", status=405)
                                    response.set_header('Allow', ', '.join(allowed_methods))
                                else:
                                    # Try custom 404 handler
                                    if 404 in self.error_handlers:
                                        response = self.error_handlers[404](request)
                                    else:
                                        response = Response("Not Found", status=404)
                            else:
                                # Call the route handler with timeout protection
                                try:
                                    if params:
                                        result = handler(request, **params)
                                    else:
                                        result = handler(request)

                                    # Convert result to Response object
                                    response = self._convert_to_response(result)

                                except Exception as handler_error:
                                    # Handle route handler errors with enhanced error handling
                                    response = self.exception_middleware.process_exception(request, handler_error)

                        # Process middleware (after request)
                        if response:
                            middleware_response = self.middleware.process_response(request, response)
                            if middleware_response:
                                response = middleware_response

                        # Run after request handlers
                        for handler in self.after_request_handlers:
                            try:
                                handler(request, response)
                            except Exception as e:
                                if self.debug:
                                    print(f"Error in after_request handler: {e}")

        except Exception as e:
            # Global exception handler
            response = self._handle_global_exception(e, environ)

        return self._finalize_response(response, start_response, start_time, request_id)
    
    def _convert_to_response(self, result: Any) -> Response:
        """
        Convert handler result to Response object.

        Args:
            result: Handler return value

        Returns:
            Response object
        """
        if isinstance(result, Response):
            return result
        elif isinstance(result, str):
            return Response(result)
        elif isinstance(result, dict):
            return Response.json(result)
        elif isinstance(result, (list, tuple)):
            return Response.json(result)
        elif result is None:
            return Response("", status=204)  # No Content
        else:
            return Response(str(result))

    def _handle_global_exception(self, exception: Exception, environ: Dict[str, Any]) -> Response:
        """
        Handle global application exceptions using enhanced error handling.

        Args:
            exception: The exception that occurred
            environ: WSGI environment

        Returns:
            Error response
        """
        # Create a minimal request object for error handling
        request = Request(environ)

        # Use the enhanced exception middleware
        return self.exception_middleware.process_exception(request, exception)

    def _finalize_response(self, response: Response, start_response: Callable, start_time: float, request_id: str = None) -> List[bytes]:
        """
        Finalize the response and record statistics.

        Args:
            response: Response object
            start_response: WSGI start_response callable
            start_time: Request start time

        Returns:
            Response body as list of bytes
        """
        if response is None:
            response = Response("Internal Server Error", status=500)

        # Record performance statistics
        response_time = time.time() - start_time
        self.record_request_stats(response.status, response_time)

        # End performance tracking
        if self.performance_manager and request_id:
            self.performance_manager.end_request(request_id, response.status)

        # Add performance headers in debug mode
        if self.debug:
            response.set_header('X-Response-Time', f"{response_time:.3f}s")
            response.set_header('X-FoxPy-Version', '0.1.0')

        # Start the response
        start_response(
            f"{response.status} {response.status_text}",
            list(response.headers.items())
        )

        # Return response body
        if isinstance(response.body, str):
            return [response.body.encode('utf-8')]
        elif isinstance(response.body, bytes):
            return [response.body]
        else:
            return [str(response.body).encode('utf-8')]

    def __call__(self, environ: Dict[str, Any], start_response: Callable):
        """Make the application callable as a WSGI app."""
        return self.wsgi_app(environ, start_response)

    async def asgi(self, scope: Dict[str, Any], receive: Callable, send: Callable):
        """ASGI application interface."""
        if self.asgi_app:
            await self.asgi_app(scope, receive, send)
        else:
            # Fallback error response
            await send({
                'type': 'http.response.start',
                'status': 501,
                'headers': [[b'content-type', b'text/plain']]
            })
            await send({
                'type': 'http.response.body',
                'body': b'ASGI support not enabled'
            })
    
    def run(self, host: str = '127.0.0.1', port: int = 8000, debug: bool = None,
            auto_reload: bool = False):
        """
        Run the development server.

        Args:
            host: Host to bind to
            port: Port to bind to
            debug: Override debug mode
            auto_reload: Enable auto-reload on file changes (development only)
        """
        if debug is not None:
            self.debug = debug

        # Auto-reload is only available in debug mode
        if auto_reload and not self.debug:
            print("Warning: Auto-reload is only available in debug mode")
            auto_reload = False

        print(f"Starting FoxPy development server on http://{host}:{port}")
        print(f"Debug mode: {'ON' if self.debug else 'OFF'}")
        if auto_reload:
            print("Auto-reload: ON")
        print("Press Ctrl+C to quit")

        try:
            if auto_reload:
                self._run_with_reloader(host, port)
            else:
                with make_server(host, port, self) as httpd:
                    httpd.serve_forever()
        except OSError as e:
            if e.errno == 10048:  # Address already in use on Windows
                print(f"Error: Port {port} is already in use")
            else:
                print(f"Error starting server: {e}")
        except KeyboardInterrupt:
            print("\nShutting down server...")

    def _run_with_reloader(self, host: str, port: int):
        """Run server with file watching for auto-reload."""
        import time
        import threading
        from pathlib import Path

        # Track file modification times
        watched_files = {}

        def watch_files():
            """Watch for file changes in the current directory."""
            while True:
                try:
                    for py_file in Path('.').rglob('*.py'):
                        if py_file.is_file():
                            mtime = py_file.stat().st_mtime
                            if str(py_file) in watched_files:
                                if watched_files[str(py_file)] != mtime:
                                    print(f"File changed: {py_file}")
                                    print("Restarting server...")
                                    os._exit(3)  # Exit code 3 for restart
                            watched_files[str(py_file)] = mtime
                    time.sleep(1)
                except Exception:
                    pass

        # Start file watcher in background
        watcher = threading.Thread(target=watch_files, daemon=True)
        watcher.start()

        # Start server
        with make_server(host, port, self) as httpd:
            httpd.serve_forever()
