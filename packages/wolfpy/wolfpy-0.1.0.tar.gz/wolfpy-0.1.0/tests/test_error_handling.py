"""
Comprehensive tests for WolfPy Error Handling System.

This test suite covers:
- Custom error pages for different HTTP status codes
- Exception middleware for global error catching
- Traceback formatting for development and production
- Error logging with different levels
- Validation error handling
- Security-aware error responses
"""

import pytest
import tempfile
import os
import json
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.wolfpy.core.error_handling import (
    ErrorContext, TracebackFormatter, ErrorLogger, ValidationErrorHandler,
    ErrorPageManager, ExceptionMiddleware
)
from src.wolfpy.core.request import Request
from src.wolfpy.core.response import Response


class TestErrorContext:
    """Test ErrorContext functionality."""
    
    def test_error_context_creation(self):
        """Test creating error context."""
        request = MagicMock()
        exception = ValueError("Test error")
        
        context = ErrorContext(
            request=request,
            exception=exception,
            status_code=400,
            message="Bad request"
        )
        
        assert context.request == request
        assert context.exception == exception
        assert context.status_code == 400
        assert context.message == "Bad request"
        assert isinstance(context.timestamp, datetime)
        assert context.details == {}
    
    def test_error_context_defaults(self):
        """Test error context with default values."""
        context = ErrorContext()
        
        assert context.request is None
        assert context.exception is None
        assert context.status_code == 500
        assert context.message == "Internal Server Error"
        assert isinstance(context.timestamp, datetime)
        assert context.details == {}


class TestTracebackFormatter:
    """Test traceback formatting functionality."""
    
    def test_production_mode_formatting(self):
        """Test traceback formatting in production mode."""
        formatter = TracebackFormatter(debug_mode=False)
        
        try:
            raise ValueError("Test error")
        except ValueError:
            exc_info = formatter.format_exception(*sys.exc_info())
        
        assert exc_info['debug'] is False
        assert exc_info['error'] == 'Internal Server Error'
        assert 'traceback' not in exc_info
        assert 'frames' not in exc_info
    
    def test_debug_mode_formatting(self):
        """Test traceback formatting in debug mode."""
        formatter = TracebackFormatter(debug_mode=True)
        
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = formatter.format_exception(*sys.exc_info())
        
        assert exc_info['debug'] is True
        assert exc_info['error'] == 'ValueError'
        assert exc_info['message'] == 'Test error'
        assert 'traceback' in exc_info
        assert 'frames' in exc_info
        assert len(exc_info['frames']) > 0
    
    def test_html_traceback_production(self):
        """Test HTML traceback in production mode."""
        formatter = TracebackFormatter(debug_mode=False)
        exc_info = {'debug': False, 'message': 'Internal Server Error'}
        
        html = formatter.format_html_traceback(exc_info)
        
        assert 'Internal Server Error' in html
        assert 'Stack Trace' not in html
        assert '<html>' in html
    
    def test_html_traceback_debug(self):
        """Test HTML traceback in debug mode."""
        formatter = TracebackFormatter(debug_mode=True)
        
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = formatter.format_exception(*sys.exc_info())
        
        request = MagicMock()
        request.method = 'GET'
        request.path = '/test'
        request.query_string = 'param=value'
        request.user_agent = 'TestAgent'
        request.remote_addr = '127.0.0.1'
        
        html = formatter.format_html_traceback(exc_info, request)
        
        assert 'ValueError' in html
        assert 'Test error' in html
        assert 'Stack Trace' in html
        assert 'Request Information' in html
        assert 'GET' in html
        assert '/test' in html


class TestErrorLogger:
    """Test error logging functionality."""
    
    def test_logger_initialization(self):
        """Test logger initialization."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            log_file = f.name
        
        try:
            logger = ErrorLogger(
                log_level='DEBUG',
                log_file=log_file,
                enable_console=True,
                enable_file=True
            )
            
            assert logger.logger.level == 10  # DEBUG level
            assert len(logger.logger.handlers) == 2  # Console + File
        finally:
            os.unlink(log_file)
    
    def test_error_logging(self):
        """Test logging error context."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            log_file = f.name
        
        try:
            logger = ErrorLogger(log_file=log_file, enable_console=False)
            
            request = MagicMock()
            request.method = 'POST'
            request.path = '/api/test'
            request.query_string = ''
            request.user_agent = 'TestAgent'
            request.remote_addr = '127.0.0.1'
            
            exception = ValueError("Test validation error")
            
            context = ErrorContext(
                request=request,
                exception=exception,
                status_code=400,
                message="Validation failed"
            )
            
            logger.log_error(context)
            
            # Check log file content
            with open(log_file, 'r') as f:
                log_content = f.read()
            
            assert 'Validation failed' in log_content
            assert 'POST' in log_content
            assert '/api/test' in log_content
            assert 'ValueError' in log_content
        finally:
            os.unlink(log_file)
    
    def test_validation_error_logging(self):
        """Test logging validation errors."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            log_file = f.name
        
        try:
            logger = ErrorLogger(log_file=log_file, enable_console=False)
            
            request = MagicMock()
            request.method = 'POST'
            request.path = '/register'
            request.remote_addr = '127.0.0.1'
            
            logger.log_validation_error('email', 'Invalid email format', 'invalid-email', request)
            
            # Check log file content
            with open(log_file, 'r') as f:
                log_content = f.read()
            
            assert 'validation_error' in log_content
            assert 'email' in log_content
            assert 'Invalid email format' in log_content
            assert 'invalid-email' in log_content
        finally:
            os.unlink(log_file)


class TestValidationErrorHandler:
    """Test validation error handling."""
    
    def test_add_single_error(self):
        """Test adding single validation error."""
        handler = ValidationErrorHandler()
        
        handler.add_error('email', 'Invalid email format')
        
        assert handler.has_errors() is True
        assert 'email' in handler.get_errors()
        assert 'Invalid email format' in handler.get_field_errors('email')
    
    def test_add_multiple_errors(self):
        """Test adding multiple validation errors."""
        handler = ValidationErrorHandler()
        
        errors = {
            'email': ['Invalid email format', 'Email already exists'],
            'password': ['Password too short']
        }
        
        handler.add_errors(errors)
        
        assert handler.has_errors() is True
        assert len(handler.get_field_errors('email')) == 2
        assert len(handler.get_field_errors('password')) == 1
    
    def test_error_response(self):
        """Test converting errors to response."""
        handler = ValidationErrorHandler()
        
        handler.add_error('email', 'Invalid email format')
        handler.add_error('password', 'Password too short')
        
        response = handler.to_response()
        
        assert response.status_code == 422
        assert response.headers['Content-Type'] == 'application/json'
        
        # Parse response data
        import json
        data = json.loads(response.body)
        
        assert data['success'] is False
        assert 'errors' in data
        assert 'email' in data['errors']
        assert 'password' in data['errors']
    
    def test_error_html(self):
        """Test converting errors to HTML."""
        handler = ValidationErrorHandler()
        
        handler.add_error('email', 'Invalid email format')
        handler.add_error('password', 'Password too short')
        
        html = handler.to_html()
        
        assert 'validation-errors' in html
        assert 'Invalid email format' in html
        assert 'Password too short' in html
        assert '<ul>' in html
        assert '<li>' in html
    
    def test_clear_errors(self):
        """Test clearing validation errors."""
        handler = ValidationErrorHandler()
        
        handler.add_error('email', 'Invalid email format')
        assert handler.has_errors() is True
        
        handler.clear()
        assert handler.has_errors() is False
        assert handler.get_errors() == {}


class TestErrorPageManager:
    """Test error page management."""
    
    def test_default_error_page(self):
        """Test generating default error page."""
        manager = ErrorPageManager(debug_mode=False)
        
        context = ErrorContext(
            status_code=404,
            message="Page not found"
        )
        
        response = manager.handle_error(404, context)
        
        assert response.status_code == 404
        assert response.headers['Content-Type'] == 'text/html'
        assert '404' in response.body
        assert 'Not Found' in response.body
    
    def test_debug_mode_error_page(self):
        """Test error page with debug information."""
        manager = ErrorPageManager(debug_mode=True)
        
        request = MagicMock()
        request.method = 'GET'
        request.path = '/nonexistent'
        request.query_string = 'param=value'
        request.user_agent = 'TestAgent'
        
        context = ErrorContext(
            request=request,
            status_code=404,
            message="Page not found"
        )
        
        response = manager.handle_error(404, context)
        
        assert response.status_code == 404
        assert 'Debug Information' in response.body
        assert 'GET' in response.body
        assert '/nonexistent' in response.body
    
    def test_custom_error_handler(self):
        """Test custom error handler registration."""
        manager = ErrorPageManager()
        
        def custom_404_handler(context):
            return Response("Custom 404 page", status=404)
        
        manager.register_handler(404, custom_404_handler)
        
        context = ErrorContext(status_code=404)
        response = manager.handle_error(404, context)
        
        assert response.status_code == 404
        assert response.body == "Custom 404 page"


class TestExceptionMiddleware:
    """Test exception middleware functionality."""

    def test_middleware_initialization(self):
        """Test middleware initialization."""
        middleware = ExceptionMiddleware(debug_mode=True)

        assert middleware.debug_mode is True
        assert middleware.logger is not None
        assert middleware.error_page_manager is not None
        assert middleware.traceback_formatter is not None

    def test_exception_status_mapping(self):
        """Test exception to status code mapping."""
        middleware = ExceptionMiddleware()

        # Test various exception types
        test_cases = [
            (FileNotFoundError("File not found"), 404),
            (PermissionError("Access denied"), 403),
            (ValueError("Invalid value"), 400),
            (TypeError("Type error"), 400),
            (KeyError("Key not found"), 400),
            (AttributeError("Attribute error"), 500),
            (ImportError("Import error"), 500),
            (NotImplementedError("Not implemented"), 501),
            (RuntimeError("Runtime error"), 500)  # Default mapping
        ]

        for exception, expected_status in test_cases:
            status = middleware.exception_status_map.get(type(exception), 500)
            assert status == expected_status

    def test_process_exception_production(self):
        """Test exception processing in production mode."""
        middleware = ExceptionMiddleware(debug_mode=False)

        request = MagicMock()
        request.method = 'GET'
        request.path = '/test'
        request.query_string = ''
        request.user_agent = 'TestAgent'
        request.remote_addr = '127.0.0.1'

        exception = ValueError("Test error")

        response = middleware.process_exception(request, exception)

        assert response.status_code == 400
        assert response.headers['Content-Type'] == 'text/html'
        assert 'Bad Request' in response.body
        # Should not contain sensitive error details
        assert 'Test error' not in response.body

    def test_process_exception_debug(self):
        """Test exception processing in debug mode."""
        middleware = ExceptionMiddleware(debug_mode=True)

        request = MagicMock()
        request.method = 'GET'
        request.path = '/test'
        request.query_string = ''
        request.user_agent = 'TestAgent'
        request.remote_addr = '127.0.0.1'

        exception = RuntimeError("Test runtime error")

        response = middleware.process_exception(request, exception)

        assert response.status_code == 500
        assert response.headers['Content-Type'] == 'text/html'
        # Should contain detailed error information in debug mode
        assert 'RuntimeError' in response.body
        assert 'Test runtime error' in response.body
        assert 'Stack Trace' in response.body

    def test_process_request_passthrough(self):
        """Test that process_request passes through unchanged."""
        middleware = ExceptionMiddleware()
        request = MagicMock()

        result = middleware.process_request(request)
        assert result == request

    def test_process_response_passthrough(self):
        """Test that process_response passes through unchanged."""
        middleware = ExceptionMiddleware()
        request = MagicMock()
        response = MagicMock()

        result = middleware.process_response(request, response)
        assert result == response


class TestErrorScenarios:
    """Test various error scenarios and edge cases."""

    def test_nested_exception_handling(self):
        """Test handling of nested exceptions."""
        middleware = ExceptionMiddleware(debug_mode=True)

        def cause_nested_error():
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise RuntimeError("Nested error") from e

        request = MagicMock()
        request.method = 'POST'
        request.path = '/api/test'
        request.query_string = ''
        request.user_agent = 'TestAgent'
        request.remote_addr = '127.0.0.1'

        try:
            cause_nested_error()
        except RuntimeError as e:
            response = middleware.process_exception(request, e)

        assert response.status_code == 500
        assert 'RuntimeError' in response.body
        assert 'Nested error' in response.body

    def test_unicode_error_handling(self):
        """Test handling of errors with unicode characters."""
        middleware = ExceptionMiddleware(debug_mode=True)

        request = MagicMock()
        request.method = 'POST'
        request.path = '/test'
        request.query_string = ''
        request.user_agent = 'TestAgent'
        request.remote_addr = '127.0.0.1'

        # Error with unicode characters
        exception = ValueError("Error with unicode: 测试错误 🚫")

        response = middleware.process_exception(request, exception)

        assert response.status_code == 400
        assert '测试错误' in response.body
        assert '🚫' in response.body

    def test_large_error_message_handling(self):
        """Test handling of errors with very large messages."""
        middleware = ExceptionMiddleware(debug_mode=True)

        request = MagicMock()
        request.method = 'POST'
        request.path = '/test'
        request.query_string = ''
        request.user_agent = 'TestAgent'
        request.remote_addr = '127.0.0.1'

        # Very large error message
        large_message = "Error: " + "x" * 10000
        exception = ValueError(large_message)

        response = middleware.process_exception(request, exception)

        assert response.status_code == 400
        assert len(response.body) > 0  # Should handle large messages gracefully

    def test_error_logging_integration(self):
        """Test integration between error handling and logging."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            log_file = f.name

        try:
            logger = ErrorLogger(log_file=log_file, enable_console=False)
            middleware = ExceptionMiddleware(debug_mode=False, logger=logger)

            request = MagicMock()
            request.method = 'GET'
            request.path = '/error-test'
            request.query_string = 'param=value'
            request.user_agent = 'TestAgent'
            request.remote_addr = '127.0.0.1'

            exception = RuntimeError("Test logging error")

            response = middleware.process_exception(request, exception)

            # Check that error was logged
            with open(log_file, 'r') as f:
                log_content = f.read()

            assert 'RuntimeError' in log_content
            assert 'Test logging error' in log_content
            assert '/error-test' in log_content
            assert 'GET' in log_content

            # Check response
            assert response.status_code == 500
        finally:
            os.unlink(log_file)

    def test_validation_error_integration(self):
        """Test integration with validation error handling."""
        handler = ValidationErrorHandler()

        # Add validation errors
        handler.add_error('email', 'Invalid email format')
        handler.add_error('password', 'Password too short')
        handler.add_error('password', 'Password must contain numbers')

        # Test JSON response
        json_response = handler.to_response(422)
        assert json_response.status_code == 422

        data = json.loads(json_response.body)
        assert data['success'] is False
        assert len(data['errors']['email']) == 1
        assert len(data['errors']['password']) == 2

        # Test HTML response
        html = handler.to_html()
        assert 'Invalid email format' in html
        assert 'Password too short' in html
        assert 'Password must contain numbers' in html


class TestErrorHandlingIntegration:
    """Test integration of error handling with the main framework."""

    def test_error_context_with_real_request(self):
        """Test error context with real request object."""
        environ = {
            'REQUEST_METHOD': 'POST',
            'PATH_INFO': '/api/users',
            'QUERY_STRING': 'page=1&limit=10',
            'CONTENT_TYPE': 'application/json',
            'HTTP_USER_AGENT': 'TestClient/1.0',
            'REMOTE_ADDR': '192.168.1.100'
        }

        request = Request(environ)
        exception = ValueError("Invalid user data")

        context = ErrorContext(
            request=request,
            exception=exception,
            status_code=400,
            message="Validation failed"
        )

        assert context.request.method == 'POST'
        assert context.request.path == '/api/users'
        assert context.request.query_string == 'page=1&limit=10'
        assert context.exception == exception
        assert context.status_code == 400

    def test_complete_error_handling_flow(self):
        """Test complete error handling flow from exception to response."""
        # Setup components
        with tempfile.NamedTemporaryFile(delete=False) as f:
            log_file = f.name

        try:
            logger = ErrorLogger(log_file=log_file, enable_console=False)
            error_page_manager = ErrorPageManager(debug_mode=True)
            traceback_formatter = TracebackFormatter(debug_mode=True)

            middleware = ExceptionMiddleware(
                debug_mode=True,
                logger=logger,
                error_page_manager=error_page_manager,
                traceback_formatter=traceback_formatter
            )

            # Create request
            environ = {
                'REQUEST_METHOD': 'GET',
                'PATH_INFO': '/test-error',
                'QUERY_STRING': 'debug=true',
                'HTTP_USER_AGENT': 'TestBrowser/1.0',
                'REMOTE_ADDR': '127.0.0.1'
            }
            request = Request(environ)

            # Simulate exception
            exception = FileNotFoundError("Template not found")

            # Process exception
            response = middleware.process_exception(request, exception)

            # Verify response
            assert response.status_code == 404
            assert 'FileNotFoundError' in response.body
            assert 'Template not found' in response.body
            assert 'Debug Information' in response.body
            assert '/test-error' in response.body

            # Verify logging
            with open(log_file, 'r') as f:
                log_content = f.read()

            assert 'FileNotFoundError' in log_content
            assert 'Template not found' in log_content
            assert '/test-error' in log_content
        finally:
            os.unlink(log_file)


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
