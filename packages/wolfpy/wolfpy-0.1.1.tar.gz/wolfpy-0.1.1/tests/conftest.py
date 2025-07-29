"""
Pytest configuration and fixtures for WolfPy Framework tests.

This file contains shared test configuration, fixtures, and utilities
used across all test modules.
"""

import pytest
import tempfile
import os
import sys
from unittest.mock import MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def temp_db():
    """Create a temporary database file for testing."""
    db_file = tempfile.mktemp(suffix='.db')
    yield db_file
    
    # Cleanup
    if os.path.exists(db_file):
        os.unlink(db_file)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_request():
    """Create a mock HTTP request for testing."""
    request = MagicMock()
    request.method = 'GET'
    request.path = '/'
    request.query_string = ''
    request.headers = {}
    request.args = {}
    request.form = {}
    request.remote_addr = '127.0.0.1'
    request.user_agent = 'TestClient/1.0'
    
    def get_json():
        return {}
    
    request.get_json = get_json
    return request


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'TestPassword123!',
        'first_name': 'Test',
        'last_name': 'User'
    }


@pytest.fixture
def sample_post_data():
    """Sample post data for testing."""
    return {
        'title': 'Test Post',
        'content': 'This is a test post with some content.',
        'published': True
    }


# Test markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "auth: marks tests related to authentication"
    )
    config.addinivalue_line(
        "markers", "database: marks tests related to database operations"
    )
    config.addinivalue_line(
        "markers", "api: marks tests related to API functionality"
    )


# Skip tests if optional dependencies are not available
def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle optional dependencies."""
    try:
        import jwt
        jwt_available = True
    except ImportError:
        jwt_available = False
    
    try:
        import pyotp
        mfa_available = True
    except ImportError:
        mfa_available = False
    
    try:
        import bcrypt
        bcrypt_available = True
    except ImportError:
        bcrypt_available = False
    
    # Skip JWT tests if PyJWT not available
    if not jwt_available:
        skip_jwt = pytest.mark.skip(reason="PyJWT not installed")
        for item in items:
            if "jwt" in item.nodeid.lower() or "token" in item.nodeid.lower():
                item.add_marker(skip_jwt)
    
    # Skip MFA tests if pyotp not available
    if not mfa_available:
        skip_mfa = pytest.mark.skip(reason="pyotp not installed")
        for item in items:
            if "mfa" in item.nodeid.lower() or "totp" in item.nodeid.lower():
                item.add_marker(skip_mfa)
    
    # Skip bcrypt tests if bcrypt not available
    if not bcrypt_available:
        skip_bcrypt = pytest.mark.skip(reason="bcrypt not installed")
        for item in items:
            if "bcrypt" in item.nodeid.lower():
                item.add_marker(skip_bcrypt)


# Test utilities
class TestClient:
    """Simple test client for making requests to WolfPy apps."""
    
    def __init__(self, app):
        """Initialize test client with app."""
        self.app = app
    
    def request(self, method, path, headers=None, data=None, json=None):
        """Make a request to the app."""
        import io
        import json as json_module
        
        # Prepare request body
        body = ''
        content_type = 'text/plain'
        
        if json is not None:
            body = json_module.dumps(json)
            content_type = 'application/json'
        elif data is not None:
            if isinstance(data, dict):
                from urllib.parse import urlencode
                body = urlencode(data)
                content_type = 'application/x-www-form-urlencoded'
            else:
                body = str(data)
        
        # Create WSGI environ
        environ = {
            'REQUEST_METHOD': method.upper(),
            'PATH_INFO': path,
            'QUERY_STRING': '',
            'CONTENT_TYPE': content_type,
            'CONTENT_LENGTH': str(len(body)),
            'wsgi.input': io.StringIO(body),
            'HTTP_HOST': 'localhost',
            'HTTP_USER_AGENT': 'TestClient/1.0'
        }
        
        # Add custom headers
        if headers:
            for key, value in headers.items():
                environ[f'HTTP_{key.upper().replace("-", "_")}'] = value
        
        # Create request and find route
        from src.wolfpy.core.request import Request
        request = Request(environ)
        
        # Find matching route
        match = self.app.router.match(path, method.upper())
        if match is None:
            from src.wolfpy.core.response import Response
            return Response("Not Found", status=404)
        
        # Execute handler
        try:
            response = match.handler(request, **match.params)
            return response
        except Exception as e:
            from src.wolfpy.core.response import Response
            return Response(f"Internal Server Error: {str(e)}", status=500)
    
    def get(self, path, headers=None):
        """Make a GET request."""
        return self.request('GET', path, headers=headers)
    
    def post(self, path, headers=None, data=None, json=None):
        """Make a POST request."""
        return self.request('POST', path, headers=headers, data=data, json=json)
    
    def put(self, path, headers=None, data=None, json=None):
        """Make a PUT request."""
        return self.request('PUT', path, headers=headers, data=data, json=json)
    
    def delete(self, path, headers=None):
        """Make a DELETE request."""
        return self.request('DELETE', path, headers=headers)


@pytest.fixture
def test_client():
    """Create a test client factory."""
    def _create_client(app):
        return TestClient(app)
    return _create_client


# Performance testing utilities
@pytest.fixture
def benchmark_timer():
    """Simple benchmark timer for performance tests."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


# Database testing utilities
@pytest.fixture
def db_with_sample_data(temp_db):
    """Create a database with sample data for testing."""
    from src.wolfpy.core.database import Database, Model, IntegerField, StringField, EmailField
    
    db = Database(temp_db)
    
    # Define sample model
    class SampleUser(Model):
        id = IntegerField(primary_key=True)
        username = StringField(max_length=50)
        email = EmailField()
    
    # Create table
    db.create_tables(SampleUser)
    
    # Add sample data
    users = [
        SampleUser(username='alice', email='alice@example.com'),
        SampleUser(username='bob', email='bob@example.com'),
        SampleUser(username='charlie', email='charlie@example.com'),
    ]
    
    for user in users:
        user.save(db)
    
    return db, SampleUser


# Authentication testing utilities
@pytest.fixture
def auth_with_test_user():
    """Create auth system with a test user."""
    from src.wolfpy.core.auth import Auth
    
    auth = Auth(secret_key='test-secret-key')
    
    # Create test user
    user = auth.create_user(
        username='testuser',
        password='TestPassword123!',
        email='test@example.com'
    )
    
    return auth, user


# API testing utilities
@pytest.fixture
def api_framework():
    """Create API framework for testing."""
    from src.wolfpy import WolfPy
    from src.wolfpy.core.api import APIFramework
    
    app = WolfPy()
    api = APIFramework(app, enable_rate_limiting=False)  # Disable for testing
    
    return app, api
