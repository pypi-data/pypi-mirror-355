"""
WolfPy ASGI Application - Phase 11 Real-Time Support

This module provides ASGI 3.0 compatible application interface for WolfPy,
enabling support for:
- HTTP/1.1 and HTTP/2 requests
- WebSocket connections
- Async/await route handlers
- Real-time communication
- Server-sent events
- Long polling support
"""

import asyncio
import json
import time
import traceback
from typing import Dict, Any, Callable, Optional, List, Union, Awaitable
from urllib.parse import parse_qs, unquote

from .request import Request
from .response import Response
from .websocket import WebSocket, WebSocketManager
from .realtime import RealtimeManager


class ASGIRequest:
    """ASGI-compatible request object."""
    
    def __init__(self, scope: Dict[str, Any], receive: Callable, send: Callable):
        self.scope = scope
        self.receive = receive
        self.send = send
        self._body = None
        self._form_data = None
        self._json_data = None
        
    @property
    def method(self) -> str:
        """Get HTTP method."""
        return self.scope.get('method', 'GET')
    
    @property
    def path(self) -> str:
        """Get request path."""
        return self.scope.get('path', '/')
    
    @property
    def query_string(self) -> str:
        """Get query string."""
        return self.scope.get('query_string', b'').decode('utf-8')
    
    @property
    def headers(self) -> Dict[str, str]:
        """Get request headers."""
        headers = {}
        for name, value in self.scope.get('headers', []):
            headers[name.decode('utf-8').lower()] = value.decode('utf-8')
        return headers
    
    @property
    def args(self) -> Dict[str, List[str]]:
        """Get query parameters."""
        if not self.query_string:
            return {}
        return parse_qs(self.query_string)
    
    async def body(self) -> bytes:
        """Get request body."""
        if self._body is None:
            body_parts = []
            while True:
                message = await self.receive()
                if message['type'] == 'http.request':
                    body_parts.append(message.get('body', b''))
                    if not message.get('more_body', False):
                        break
                elif message['type'] == 'http.disconnect':
                    break
            self._body = b''.join(body_parts)
        return self._body
    
    async def json(self) -> Any:
        """Get JSON data from request body."""
        if self._json_data is None:
            body = await self.body()
            if body:
                try:
                    self._json_data = json.loads(body.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    self._json_data = {}
            else:
                self._json_data = {}
        return self._json_data
    
    async def form(self) -> Dict[str, str]:
        """Get form data from request body."""
        if self._form_data is None:
            body = await self.body()
            if body:
                try:
                    form_data = parse_qs(body.decode('utf-8'))
                    # Convert lists to single values for simplicity
                    self._form_data = {k: v[0] if v else '' for k, v in form_data.items()}
                except UnicodeDecodeError:
                    self._form_data = {}
            else:
                self._form_data = {}
        return self._form_data


class ASGIResponse:
    """ASGI-compatible response object."""
    
    def __init__(self, body: Union[str, bytes] = "", status: int = 200, 
                 headers: Optional[Dict[str, str]] = None, content_type: str = "text/html"):
        self.body = body
        self.status = status
        self.headers = headers or {}
        if 'content-type' not in self.headers:
            self.headers['content-type'] = content_type
    
    async def send_response(self, send: Callable):
        """Send ASGI response."""
        # Send response start
        await send({
            'type': 'http.response.start',
            'status': self.status,
            'headers': [
                [name.encode(), value.encode()]
                for name, value in self.headers.items()
            ]
        })
        
        # Send response body
        body_bytes = self.body.encode('utf-8') if isinstance(self.body, str) else self.body
        await send({
            'type': 'http.response.body',
            'body': body_bytes
        })
    
    @classmethod
    def json(cls, data: Any, status: int = 200, headers: Optional[Dict[str, str]] = None):
        """Create JSON response."""
        headers = headers or {}
        headers['content-type'] = 'application/json'
        return cls(
            body=json.dumps(data, default=str),
            status=status,
            headers=headers
        )
    
    @classmethod
    def text(cls, text: str, status: int = 200, headers: Optional[Dict[str, str]] = None):
        """Create text response."""
        headers = headers or {}
        headers['content-type'] = 'text/plain'
        return cls(body=text, status=status, headers=headers)
    
    @classmethod
    def html(cls, html: str, status: int = 200, headers: Optional[Dict[str, str]] = None):
        """Create HTML response."""
        headers = headers or {}
        headers['content-type'] = 'text/html'
        return cls(body=html, status=status, headers=headers)


class ASGIApplication:
    """
    ASGI 3.0 compatible application for WolfPy.
    
    Supports:
    - HTTP requests (sync and async handlers)
    - WebSocket connections
    - Real-time communication
    - Middleware processing
    """
    
    def __init__(self, wolfpy_app):
        """Initialize ASGI application with WolfPy app instance."""
        self.wolfpy_app = wolfpy_app
        self.websocket_manager = WebSocketManager()
        self.realtime_manager = RealtimeManager()
        self.async_routes = {}
        self.websocket_routes = {}
        
        # Setup default error handlers
        self.error_handlers = {
            404: self._default_404_handler,
            500: self._default_500_handler
        }
    
    def add_async_route(self, path: str, handler: Callable, methods: List[str] = None):
        """Add async route handler."""
        methods = methods or ['GET']
        for method in methods:
            key = f"{method.upper()}:{path}"
            self.async_routes[key] = handler
    
    def add_websocket_route(self, path: str, handler: Callable):
        """Add WebSocket route handler."""
        self.websocket_routes[path] = handler
    
    def websocket(self, path: str):
        """Decorator for WebSocket routes."""
        def decorator(handler):
            self.add_websocket_route(path, handler)
            return handler
        return decorator
    
    def async_route(self, path: str, methods: List[str] = None):
        """Decorator for async HTTP routes."""
        def decorator(handler):
            self.add_async_route(path, handler, methods)
            return handler
        return decorator
    
    async def __call__(self, scope: Dict[str, Any], receive: Callable, send: Callable):
        """ASGI application entry point."""
        if scope['type'] == 'http':
            await self._handle_http(scope, receive, send)
        elif scope['type'] == 'websocket':
            await self._handle_websocket(scope, receive, send)
        else:
            # Unsupported protocol
            await send({
                'type': 'http.response.start',
                'status': 501,
                'headers': [[b'content-type', b'text/plain']]
            })
            await send({
                'type': 'http.response.body',
                'body': b'Protocol not supported'
            })
    
    async def _handle_http(self, scope: Dict[str, Any], receive: Callable, send: Callable):
        """Handle HTTP requests."""
        request = ASGIRequest(scope, receive, send)
        
        try:
            # Check for async routes first
            route_key = f"{request.method}:{request.path}"
            if route_key in self.async_routes:
                handler = self.async_routes[route_key]
                response = await handler(request)
            else:
                # Fall back to WSGI app for sync routes
                response = await self._handle_wsgi_fallback(scope, receive, send)
                return
            
            # Send response
            if isinstance(response, ASGIResponse):
                await response.send_response(send)
            elif isinstance(response, dict):
                await ASGIResponse.json(response).send_response(send)
            elif isinstance(response, str):
                await ASGIResponse.html(response).send_response(send)
            else:
                await ASGIResponse.text(str(response)).send_response(send)
                
        except Exception as e:
            await self._handle_error(e, send)
    
    async def _handle_websocket(self, scope: Dict[str, Any], receive: Callable, send: Callable):
        """Handle WebSocket connections."""
        path = scope.get('path', '/')
        
        if path in self.websocket_routes:
            websocket = WebSocket(scope, receive, send)
            handler = self.websocket_routes[path]
            
            try:
                # Accept connection
                await websocket.accept()
                
                # Register with manager
                self.websocket_manager.add_connection(websocket)
                
                # Handle connection
                await handler(websocket)
                
            except Exception as e:
                print(f"WebSocket error: {e}")
                await websocket.close(code=1011, reason="Internal server error")
            finally:
                # Cleanup
                self.websocket_manager.remove_connection(websocket)
        else:
            # No handler found
            await send({
                'type': 'websocket.close',
                'code': 1000
            })
    
    async def _handle_wsgi_fallback(self, scope: Dict[str, Any], receive: Callable, send: Callable):
        """Handle request through WSGI app (for sync routes)."""
        # Convert ASGI scope to WSGI environ
        environ = self._asgi_to_wsgi_environ(scope)
        
        # Create a simple start_response function
        response_started = False
        status = None
        headers = []
        
        def start_response(status_line, response_headers, exc_info=None):
            nonlocal response_started, status, headers
            if response_started:
                raise RuntimeError("Response already started")
            response_started = True
            status = int(status_line.split(' ', 1)[0])
            headers = response_headers
        
        # Get request body for WSGI
        body_parts = []
        while True:
            message = await receive()
            if message['type'] == 'http.request':
                body_parts.append(message.get('body', b''))
                if not message.get('more_body', False):
                    break
            elif message['type'] == 'http.disconnect':
                break
        
        body = b''.join(body_parts)
        environ['wsgi.input'] = type('MockInput', (), {
            'read': lambda self, size=-1: body,
            'readline': lambda self: b'',
            'readlines': lambda self: []
        })()
        environ['CONTENT_LENGTH'] = str(len(body))
        
        # Call WSGI app
        response_iter = self.wolfpy_app.wsgi_app(environ, start_response)
        
        # Send ASGI response
        await send({
            'type': 'http.response.start',
            'status': status,
            'headers': [[name.encode(), value.encode()] for name, value in headers]
        })
        
        for chunk in response_iter:
            await send({
                'type': 'http.response.body',
                'body': chunk
            })
    
    def _asgi_to_wsgi_environ(self, scope: Dict[str, Any]) -> Dict[str, Any]:
        """Convert ASGI scope to WSGI environ."""
        environ = {
            'REQUEST_METHOD': scope['method'],
            'SCRIPT_NAME': '',
            'PATH_INFO': scope['path'],
            'QUERY_STRING': scope.get('query_string', b'').decode('latin1'),
            'CONTENT_TYPE': '',
            'CONTENT_LENGTH': '',
            'SERVER_NAME': scope.get('server', ['localhost', None])[0],
            'SERVER_PORT': str(scope.get('server', [None, 80])[1]),
            'SERVER_PROTOCOL': f"HTTP/{scope.get('http_version', '1.1')}",
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': scope.get('scheme', 'http'),
            'wsgi.input': None,  # Will be set later
            'wsgi.errors': None,
            'wsgi.multithread': True,
            'wsgi.multiprocess': False,
            'wsgi.run_once': False,
        }
        
        # Add headers
        for name, value in scope.get('headers', []):
            name = name.decode('latin1')
            value = value.decode('latin1')
            
            if name.lower() == 'content-type':
                environ['CONTENT_TYPE'] = value
            elif name.lower() == 'content-length':
                environ['CONTENT_LENGTH'] = value
            else:
                # Convert to CGI-style header name
                key = f"HTTP_{name.upper().replace('-', '_')}"
                environ[key] = value
        
        return environ
    
    async def _handle_error(self, error: Exception, send: Callable):
        """Handle application errors."""
        print(f"ASGI Error: {error}")
        traceback.print_exc()
        
        await send({
            'type': 'http.response.start',
            'status': 500,
            'headers': [[b'content-type', b'application/json']]
        })
        
        error_response = {
            'error': 'Internal Server Error',
            'message': str(error) if self.wolfpy_app.debug else 'An error occurred'
        }
        
        await send({
            'type': 'http.response.body',
            'body': json.dumps(error_response).encode('utf-8')
        })
    
    async def _default_404_handler(self, request: ASGIRequest) -> ASGIResponse:
        """Default 404 handler."""
        return ASGIResponse.json({
            'error': 'Not Found',
            'message': f'The requested URL {request.path} was not found.'
        }, status=404)
    
    async def _default_500_handler(self, request: ASGIRequest, error: Exception) -> ASGIResponse:
        """Default 500 handler."""
        return ASGIResponse.json({
            'error': 'Internal Server Error',
            'message': str(error) if self.wolfpy_app.debug else 'An error occurred'
        }, status=500)
