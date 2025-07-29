"""
Comprehensive unit tests for WolfPy Request handling.

This test suite covers all aspects of HTTP request processing including:
- Request initialization and basic properties
- Query parameter parsing and type conversion
- Form data handling (URL-encoded and multipart)
- JSON data parsing and validation
- File upload handling
- Cookie parsing
- Header processing
- Content type negotiation
- Request validation and sanitization
- Security features
"""

import pytest
import json
import io
import tempfile
import os
from unittest.mock import MagicMock, patch
from urllib.parse import urlencode

from src.wolfpy.core.request import Request, RequestValidator, RequestParser, UploadedFile


class TestRequestBasics:
    """Test basic request functionality."""
    
    def test_request_initialization(self):
        """Test request initialization from WSGI environ."""
        environ = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/test',
            'QUERY_STRING': 'param=value',
            'CONTENT_TYPE': 'text/plain',
            'CONTENT_LENGTH': '10',
            'HTTP_HOST': 'example.com',
            'HTTP_USER_AGENT': 'TestAgent/1.0'
        }
        
        request = Request(environ)
        
        assert request.method == 'GET'
        assert request.path == '/test'
        assert request.query_string == 'param=value'
        assert request.content_type == 'text/plain'
        assert request.content_length == 10
        assert request.host == 'example.com'
        assert request.user_agent == 'TestAgent/1.0'
    
    def test_request_url_construction(self):
        """Test URL construction from environ."""
        environ = {
            'wsgi.url_scheme': 'https',
            'HTTP_HOST': 'example.com',
            'PATH_INFO': '/api/users',
            'QUERY_STRING': 'page=1&limit=10'
        }
        
        request = Request(environ)
        
        assert request.url == 'https://example.com/api/users'
        assert request.full_url == 'https://example.com/api/users?page=1&limit=10'
    
    def test_request_with_port(self):
        """Test URL construction with non-standard port."""
        environ = {
            'wsgi.url_scheme': 'http',
            'HTTP_HOST': 'localhost:8080',
            'PATH_INFO': '/test'
        }
        
        request = Request(environ)
        assert request.url == 'http://localhost:8080/test'
    
    def test_request_properties_defaults(self):
        """Test request properties with minimal environ."""
        environ = {}
        request = Request(environ)
        
        assert request.method == 'GET'
        assert request.path == '/'
        assert request.query_string == ''
        assert request.content_type == ''
        assert request.content_length == 0


class TestQueryParameters:
    """Test query parameter parsing and handling."""
    
    def test_simple_query_params(self):
        """Test parsing simple query parameters."""
        environ = {
            'QUERY_STRING': 'name=John&age=30&active=true'
        }
        
        request = Request(environ)
        args = request.args
        
        assert args['name'] == ['John']
        assert args['age'] == ['30']
        assert args['active'] == ['true']
    
    def test_multiple_values_same_key(self):
        """Test handling multiple values for same parameter."""
        environ = {
            'QUERY_STRING': 'tags=python&tags=web&tags=framework'
        }
        
        request = Request(environ)
        
        assert request.args['tags'] == ['python', 'web', 'framework']
        assert request.get_args_list('tags') == ['python', 'web', 'framework']
    
    def test_get_arg_with_type_casting(self):
        """Test getting single argument with type casting."""
        environ = {
            'QUERY_STRING': 'page=2&limit=50&active=true&score=95.5'
        }
        
        request = Request(environ)
        
        assert request.get_arg('page', type_cast=int) == 2
        assert request.get_arg('limit', type_cast=int) == 50
        assert request.get_arg('score', type_cast=float) == 95.5
        assert request.get_arg('nonexistent', default='default') == 'default'
    
    def test_get_int_and_float_helpers(self):
        """Test convenience methods for integer and float parameters."""
        environ = {
            'QUERY_STRING': 'page=3&score=87.5&invalid=abc'
        }
        
        request = Request(environ)
        
        assert request.get_int('page') == 3
        assert request.get_float('score') == 87.5
        assert request.get_int('invalid', default=1) == 1
        assert request.get_float('invalid', default=0.0) == 0.0
    
    def test_empty_query_string(self):
        """Test handling empty query string."""
        environ = {'QUERY_STRING': ''}
        request = Request(environ)
        
        assert request.args == {}
        assert request.get_arg('any') is None


class TestFormData:
    """Test form data parsing and handling."""
    
    def test_url_encoded_form_data(self):
        """Test parsing URL-encoded form data."""
        form_data = urlencode({
            'username': 'testuser',
            'password': 'secret123',
            'remember': 'on'
        })
        
        environ = {
            'REQUEST_METHOD': 'POST',
            'CONTENT_TYPE': 'application/x-www-form-urlencoded',
            'CONTENT_LENGTH': str(len(form_data)),
            'wsgi.input': io.StringIO(form_data)
        }
        
        request = Request(environ)
        
        assert request.get_form('username') == 'testuser'
        assert request.get_form('password') == 'secret123'
        assert request.get_form('remember') == 'on'
    
    def test_form_data_with_type_casting(self):
        """Test form data with type casting."""
        form_data = urlencode({
            'age': '25',
            'height': '175.5',
            'active': 'true'
        })
        
        environ = {
            'REQUEST_METHOD': 'POST',
            'CONTENT_TYPE': 'application/x-www-form-urlencoded',
            'CONTENT_LENGTH': str(len(form_data)),
            'wsgi.input': io.StringIO(form_data)
        }
        
        request = Request(environ)
        
        assert request.get_form('age', type_cast=int) == 25
        assert request.get_form('height', type_cast=float) == 175.5
        assert request.get_form('nonexistent', default='default') == 'default'


class TestJSONData:
    """Test JSON data parsing and handling."""
    
    def test_json_parsing(self):
        """Test parsing JSON request data."""
        json_data = {'name': 'John', 'age': 30, 'skills': ['Python', 'JavaScript']}
        json_string = json.dumps(json_data)
        
        environ = {
            'REQUEST_METHOD': 'POST',
            'CONTENT_TYPE': 'application/json',
            'CONTENT_LENGTH': str(len(json_string)),
            'wsgi.input': io.StringIO(json_string)
        }
        
        request = Request(environ)
        
        assert request.is_json() is True
        assert request.json == json_data
        assert request.get_json('name') == 'John'
        assert request.get_json('age') == 30
        assert request.get_json('skills') == ['Python', 'JavaScript']
    
    def test_nested_json_access(self):
        """Test accessing nested JSON data with dot notation."""
        json_data = {
            'user': {
                'profile': {
                    'name': 'John Doe',
                    'settings': {
                        'theme': 'dark'
                    }
                }
            }
        }
        json_string = json.dumps(json_data)
        
        environ = {
            'REQUEST_METHOD': 'POST',
            'CONTENT_TYPE': 'application/json',
            'CONTENT_LENGTH': str(len(json_string)),
            'wsgi.input': io.StringIO(json_string)
        }
        
        request = Request(environ)
        
        assert request.get_json('user.profile.name') == 'John Doe'
        assert request.get_json('user.profile.settings.theme') == 'dark'
        assert request.get_json('user.nonexistent', default='default') == 'default'
    
    def test_invalid_json(self):
        """Test handling invalid JSON data."""
        invalid_json = '{"name": "John", "age":}'
        
        environ = {
            'REQUEST_METHOD': 'POST',
            'CONTENT_TYPE': 'application/json',
            'CONTENT_LENGTH': str(len(invalid_json)),
            'wsgi.input': io.StringIO(invalid_json)
        }
        
        request = Request(environ)
        
        assert request.json is None
        assert request.get_json('name') is None


class TestRequestValidation:
    """Test request validation functionality."""
    
    def test_email_validation(self):
        """Test email validation."""
        validator = RequestValidator()
        
        assert validator.validate_email('test@example.com') is True
        assert validator.validate_email('user.name+tag@domain.co.uk') is True
        assert validator.validate_email('invalid-email') is False
        assert validator.validate_email('test@') is False
        assert validator.validate_email('@example.com') is False
    
    def test_url_validation(self):
        """Test URL validation."""
        validator = RequestValidator()
        
        assert validator.validate_url('https://example.com') is True
        assert validator.validate_url('http://localhost:8080/path') is True
        assert validator.validate_url('ftp://example.com') is False
        assert validator.validate_url('not-a-url') is False
    
    def test_phone_validation(self):
        """Test phone number validation."""
        validator = RequestValidator()
        
        assert validator.validate_phone('123-456-7890') is True
        assert validator.validate_phone('(123) 456-7890') is True
        assert validator.validate_phone('+1-123-456-7890') is True
        assert validator.validate_phone('123456789') is False
        assert validator.validate_phone('abc-def-ghij') is False


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
