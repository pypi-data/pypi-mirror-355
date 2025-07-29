"""
Comprehensive Error Handling System for WolfPy Framework.

This module provides:
- Custom error pages for different HTTP status codes
- Exception middleware for global error catching
- Traceback formatting for development and production
- Error logging with different levels and providers
- Validation error handling
- Security-aware error responses
"""

import traceback
import logging
import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List, Union
from dataclasses import dataclass

from .response import Response
from .request import Request


@dataclass
class ErrorContext:
    """Context information for error handling."""
    request: Optional[Request] = None
    exception: Optional[Exception] = None
    status_code: int = 500
    message: str = "Internal Server Error"
    details: Dict[str, Any] = None
    timestamp: datetime = None
    request_id: str = None
    user_id: str = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
        if self.timestamp is None:
            self.timestamp = datetime.now()


class TracebackFormatter:
    """Formats tracebacks for different environments."""
    
    def __init__(self, debug_mode: bool = False, show_locals: bool = False):
        """
        Initialize traceback formatter.
        
        Args:
            debug_mode: Whether to show detailed tracebacks
            show_locals: Whether to include local variables in traceback
        """
        self.debug_mode = debug_mode
        self.show_locals = show_locals
    
    def format_exception(self, exc_type, exc_value, exc_traceback) -> Dict[str, Any]:
        """
        Format exception information.
        
        Returns:
            Dictionary with formatted exception details
        """
        if not self.debug_mode:
            return {
                'error': 'Internal Server Error',
                'message': 'An error occurred while processing your request.',
                'debug': False
            }
        
        # Extract traceback information
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        
        # Parse stack frames
        frames = []
        tb = exc_traceback
        while tb is not None:
            frame = tb.tb_frame
            filename = frame.f_code.co_filename
            line_number = tb.tb_lineno
            function_name = frame.f_code.co_name
            
            # Get source code context
            try:
                with open(filename, 'r') as f:
                    lines = f.readlines()
                    start = max(0, line_number - 3)
                    end = min(len(lines), line_number + 2)
                    context = {
                        'pre': lines[start:line_number-1],
                        'line': lines[line_number-1] if line_number <= len(lines) else '',
                        'post': lines[line_number:end]
                    }
            except (IOError, IndexError):
                context = None
            
            frame_info = {
                'filename': os.path.basename(filename),
                'full_path': filename,
                'line_number': line_number,
                'function': function_name,
                'context': context
            }
            
            # Add local variables if requested
            if self.show_locals:
                frame_info['locals'] = {
                    k: repr(v) for k, v in frame.f_locals.items()
                    if not k.startswith('__')
                }
            
            frames.append(frame_info)
            tb = tb.tb_next
        
        return {
            'error': exc_type.__name__,
            'message': str(exc_value),
            'traceback': ''.join(tb_lines),
            'frames': frames,
            'debug': True
        }
    
    def format_html_traceback(self, exc_info: Dict[str, Any], request: Request = None) -> str:
        """
        Format exception as HTML for browser display.
        
        Args:
            exc_info: Exception information from format_exception
            request: Request object for context
            
        Returns:
            HTML formatted error page
        """
        if not exc_info.get('debug', False):
            return self._simple_error_page(exc_info.get('message', 'Internal Server Error'))
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>WolfPy Debug - {exc_info['error']}</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: #dc3545; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ padding: 20px; }}
                .error-title {{ margin: 0; font-size: 24px; }}
                .error-message {{ margin: 5px 0 0 0; font-size: 16px; opacity: 0.9; }}
                .section {{ margin: 20px 0; }}
                .section-title {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #333; }}
                .frame {{ background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px; margin: 10px 0; }}
                .frame-header {{ background: #e9ecef; padding: 10px; border-bottom: 1px solid #dee2e6; }}
                .frame-content {{ padding: 10px; }}
                .code-context {{ background: #2d3748; color: #e2e8f0; padding: 10px; border-radius: 4px; overflow-x: auto; }}
                .code-line {{ margin: 2px 0; }}
                .code-line.current {{ background: #e53e3e; color: white; font-weight: bold; }}
                .request-info {{ background: #e3f2fd; padding: 15px; border-radius: 4px; }}
                .locals {{ background: #fff3cd; padding: 10px; border-radius: 4px; margin-top: 10px; }}
                pre {{ margin: 0; white-space: pre-wrap; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 class="error-title">{exc_info['error']}</h1>
                    <p class="error-message">{exc_info['message']}</p>
                </div>
                <div class="content">
        """
        
        # Request information
        if request:
            html += f"""
                    <div class="section">
                        <div class="section-title">Request Information</div>
                        <div class="request-info">
                            <strong>Method:</strong> {request.method}<br>
                            <strong>Path:</strong> {request.path}<br>
                            <strong>Query String:</strong> {request.query_string}<br>
                            <strong>User Agent:</strong> {request.user_agent}<br>
                            <strong>Remote Address:</strong> {request.remote_addr}
                        </div>
                    </div>
            """
        
        # Stack trace
        html += """
                    <div class="section">
                        <div class="section-title">Stack Trace</div>
        """
        
        for i, frame in enumerate(exc_info.get('frames', [])):
            html += f"""
                        <div class="frame">
                            <div class="frame-header">
                                <strong>{frame['filename']}</strong> in <strong>{frame['function']}</strong> at line <strong>{frame['line_number']}</strong>
                            </div>
                            <div class="frame-content">
            """
            
            # Code context
            if frame.get('context'):
                html += '<div class="code-context">'
                
                # Pre-lines
                for j, line in enumerate(frame['context'].get('pre', [])):
                    line_num = frame['line_number'] - len(frame['context']['pre']) + j
                    html += f'<div class="code-line">{line_num:4d}: {line.rstrip()}</div>'
                
                # Current line
                current_line = frame['context'].get('line', '').rstrip()
                html += f'<div class="code-line current">{frame["line_number"]:4d}: {current_line}</div>'
                
                # Post-lines
                for j, line in enumerate(frame['context'].get('post', [])):
                    line_num = frame['line_number'] + j + 1
                    html += f'<div class="code-line">{line_num:4d}: {line.rstrip()}</div>'
                
                html += '</div>'
            
            # Local variables
            if frame.get('locals'):
                html += '<div class="locals"><strong>Local Variables:</strong><br>'
                for var_name, var_value in frame['locals'].items():
                    html += f'<strong>{var_name}:</strong> {var_value}<br>'
                html += '</div>'
            
            html += """
                            </div>
                        </div>
            """
        
        html += """
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _simple_error_page(self, message: str) -> str:
        """Generate simple error page for production."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                .error {{ color: #721c24; background: #f8d7da; padding: 20px; border-radius: 5px; display: inline-block; }}
            </style>
        </head>
        <body>
            <div class="error">
                <h1>Oops! Something went wrong</h1>
                <p>{message}</p>
            </div>
        </body>
        </html>
        """


class ErrorLogger:
    """Handles error logging with different levels and providers."""
    
    def __init__(self, 
                 log_level: str = 'INFO',
                 log_file: str = None,
                 enable_console: bool = True,
                 enable_file: bool = True,
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5):
        """
        Initialize error logger.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Path to log file
            enable_console: Whether to log to console
            enable_file: Whether to log to file
            max_file_size: Maximum log file size before rotation
            backup_count: Number of backup files to keep
        """
        self.logger = logging.getLogger('wolfpy.errors')
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
        
        # File handler with rotation
        if enable_file and log_file:
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                log_file, maxBytes=max_file_size, backupCount=backup_count
            )
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def log_error(self, error_context: ErrorContext):
        """Log error with context information."""
        log_data = {
            'status_code': error_context.status_code,
            'message': error_context.message,
            'timestamp': error_context.timestamp.isoformat(),
            'request_id': error_context.request_id,
            'user_id': error_context.user_id,
            'details': error_context.details
        }
        
        if error_context.request:
            log_data['request'] = {
                'method': error_context.request.method,
                'path': error_context.request.path,
                'query_string': error_context.request.query_string,
                'user_agent': error_context.request.user_agent,
                'remote_addr': error_context.request.remote_addr
            }
        
        if error_context.exception:
            log_data['exception'] = {
                'type': type(error_context.exception).__name__,
                'message': str(error_context.exception),
                'traceback': traceback.format_exc()
            }
        
        # Log based on status code
        if error_context.status_code >= 500:
            self.logger.error(json.dumps(log_data, indent=2))
        elif error_context.status_code >= 400:
            self.logger.warning(json.dumps(log_data, indent=2))
        else:
            self.logger.info(json.dumps(log_data, indent=2))
    
    def log_validation_error(self, field: str, message: str, value: Any = None, request: Request = None):
        """Log validation errors."""
        log_data = {
            'type': 'validation_error',
            'field': field,
            'message': message,
            'value': repr(value) if value is not None else None,
            'timestamp': datetime.now().isoformat()
        }
        
        if request:
            log_data['request'] = {
                'method': request.method,
                'path': request.path,
                'remote_addr': request.remote_addr
            }
        
        self.logger.warning(json.dumps(log_data, indent=2))


class ValidationErrorHandler:
    """Handles validation errors with standardized formatting."""

    def __init__(self):
        """Initialize validation error handler."""
        self.errors = {}

    def add_error(self, field: str, message: str):
        """Add a validation error for a field."""
        if field not in self.errors:
            self.errors[field] = []
        self.errors[field].append(message)

    def add_errors(self, errors: Dict[str, List[str]]):
        """Add multiple validation errors."""
        for field, messages in errors.items():
            for message in messages:
                self.add_error(field, message)

    def has_errors(self) -> bool:
        """Check if there are any validation errors."""
        return bool(self.errors)

    def get_errors(self) -> Dict[str, List[str]]:
        """Get all validation errors."""
        return self.errors.copy()

    def get_field_errors(self, field: str) -> List[str]:
        """Get errors for a specific field."""
        return self.errors.get(field, [])

    def clear(self):
        """Clear all validation errors."""
        self.errors.clear()

    def to_response(self, status_code: int = 422) -> Response:
        """Convert validation errors to HTTP response."""
        return Response.json({
            'success': False,
            'errors': self.errors,
            'message': 'Validation failed'
        }, status=status_code)

    def to_html(self) -> str:
        """Convert validation errors to HTML format."""
        if not self.errors:
            return ""

        html = '<div class="validation-errors alert alert-danger">'
        html += '<h4>Please correct the following errors:</h4>'
        html += '<ul>'

        for field, messages in self.errors.items():
            for message in messages:
                html += f'<li><strong>{field}:</strong> {message}</li>'

        html += '</ul></div>'
        return html


class ErrorPageManager:
    """Manages custom error pages for different HTTP status codes."""

    def __init__(self, template_engine=None, debug_mode: bool = False):
        """
        Initialize error page manager.

        Args:
            template_engine: Template engine for rendering custom error pages
            debug_mode: Whether to show debug information
        """
        self.template_engine = template_engine
        self.debug_mode = debug_mode
        self.custom_handlers = {}
        self.default_templates = {
            400: 'errors/400.html',
            401: 'errors/401.html',
            403: 'errors/403.html',
            404: 'errors/404.html',
            405: 'errors/405.html',
            422: 'errors/422.html',
            500: 'errors/500.html',
            502: 'errors/502.html',
            503: 'errors/503.html'
        }

    def register_handler(self, status_code: int, handler: Callable):
        """Register custom error handler for status code."""
        self.custom_handlers[status_code] = handler

    def handle_error(self, status_code: int, error_context: ErrorContext) -> Response:
        """
        Handle error and return appropriate response.

        Args:
            status_code: HTTP status code
            error_context: Error context information

        Returns:
            Response object with error page
        """
        # Try custom handler first
        if status_code in self.custom_handlers:
            try:
                return self.custom_handlers[status_code](error_context)
            except Exception:
                # Fall back to default handling if custom handler fails
                pass

        # Try template rendering
        if self.template_engine and status_code in self.default_templates:
            try:
                template_name = self.default_templates[status_code]
                context = {
                    'status_code': status_code,
                    'message': error_context.message,
                    'debug': self.debug_mode,
                    'request': error_context.request,
                    'error': error_context.exception,
                    'timestamp': error_context.timestamp
                }

                content = self.template_engine.render(template_name, context)
                return Response(content, status=status_code, headers={'Content-Type': 'text/html'})
            except Exception:
                # Fall back to default HTML if template fails
                pass

        # Default HTML error pages
        return self._default_error_page(status_code, error_context)

    def _default_error_page(self, status_code: int, error_context: ErrorContext) -> Response:
        """Generate default error page."""
        status_messages = {
            400: 'Bad Request',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not Found',
            405: 'Method Not Allowed',
            422: 'Unprocessable Entity',
            500: 'Internal Server Error',
            502: 'Bad Gateway',
            503: 'Service Unavailable'
        }

        title = status_messages.get(status_code, 'Error')
        message = error_context.message or title

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{status_code} - {title}</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0; padding: 0; background: #f8f9fa;
                    display: flex; align-items: center; justify-content: center;
                    min-height: 100vh;
                }}
                .error-container {{
                    text-align: center; background: white;
                    padding: 40px; border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    max-width: 500px;
                }}
                .error-code {{
                    font-size: 72px; font-weight: bold;
                    color: #dc3545; margin: 0;
                }}
                .error-title {{
                    font-size: 24px; color: #333;
                    margin: 10px 0;
                }}
                .error-message {{
                    color: #666; margin: 20px 0;
                    line-height: 1.5;
                }}
                .error-actions {{ margin-top: 30px; }}
                .btn {{
                    display: inline-block; padding: 10px 20px;
                    background: #007bff; color: white;
                    text-decoration: none; border-radius: 4px;
                    transition: background 0.3s;
                }}
                .btn:hover {{ background: #0056b3; }}
                .debug-info {{
                    background: #f8f9fa; padding: 15px;
                    border-radius: 4px; margin-top: 20px;
                    text-align: left; font-family: monospace;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <div class="error-code">{status_code}</div>
                <div class="error-title">{title}</div>
                <div class="error-message">{message}</div>
                <div class="error-actions">
                    <a href="/" class="btn">Go Home</a>
                </div>
        """

        # Add debug information if in debug mode
        if self.debug_mode and error_context.request:
            html += f"""
                <div class="debug-info">
                    <strong>Debug Information:</strong><br>
                    <strong>Method:</strong> {error_context.request.method}<br>
                    <strong>Path:</strong> {error_context.request.path}<br>
                    <strong>Query:</strong> {error_context.request.query_string}<br>
                    <strong>User Agent:</strong> {error_context.request.user_agent}<br>
                    <strong>Timestamp:</strong> {error_context.timestamp}
                </div>
            """

        html += """
            </div>
        </body>
        </html>
        """

        return Response(html, status=status_code, headers={'Content-Type': 'text/html'})


class ExceptionMiddleware:
    """Middleware for global exception handling."""

    def __init__(self,
                 debug_mode: bool = False,
                 logger: ErrorLogger = None,
                 error_page_manager: ErrorPageManager = None,
                 traceback_formatter: TracebackFormatter = None):
        """
        Initialize exception middleware.

        Args:
            debug_mode: Whether to show detailed error information
            logger: Error logger instance
            error_page_manager: Error page manager instance
            traceback_formatter: Traceback formatter instance
        """
        self.debug_mode = debug_mode
        self.logger = logger or ErrorLogger()
        self.error_page_manager = error_page_manager or ErrorPageManager(debug_mode=debug_mode)
        self.traceback_formatter = traceback_formatter or TracebackFormatter(debug_mode=debug_mode)

        # Exception to status code mapping
        self.exception_status_map = {
            FileNotFoundError: 404,
            PermissionError: 403,
            ValueError: 400,
            TypeError: 400,
            KeyError: 400,
            AttributeError: 500,
            ImportError: 500,
            NotImplementedError: 501
        }

    def process_request(self, request: Request):
        """Process request (no-op for exception middleware)."""
        return request

    def process_response(self, request: Request, response: Response):
        """Process response (no-op for exception middleware)."""
        return response

    def process_exception(self, request: Request, exception: Exception) -> Response:
        """
        Process exception and return error response.

        Args:
            request: Request object
            exception: Exception that occurred

        Returns:
            Response object with error page
        """
        # Determine status code
        status_code = self.exception_status_map.get(type(exception), 500)

        # Create error context
        error_context = ErrorContext(
            request=request,
            exception=exception,
            status_code=status_code,
            message=str(exception) if self.debug_mode else None
        )

        # Log the error
        self.logger.log_error(error_context)

        # Handle specific error types
        if status_code == 500 and self.debug_mode:
            # Show detailed traceback for 500 errors in debug mode
            exc_info = self.traceback_formatter.format_exception(
                type(exception), exception, exception.__traceback__
            )
            html_content = self.traceback_formatter.format_html_traceback(exc_info, request)
            return Response(html_content, status=500, headers={'Content-Type': 'text/html'})

        # Use error page manager for other cases
        return self.error_page_manager.handle_error(status_code, error_context)
