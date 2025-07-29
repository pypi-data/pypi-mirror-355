"""
Tests for WolfPy Core Framework Components.

This test suite covers the core framework functionality including:
- Application setup and configuration
- Request and response handling
- Routing and middleware
- Template rendering
- Static file serving
"""

import pytest
import tempfile
import os
from unittest.mock import MagicMock, patch

from src.wolfpy import WolfPy
from src.wolfpy.core.request import Request
from src.wolfpy.core.response import Response
from src.wolfpy.core.router import Router
from src.wolfpy.core.template_engine import TemplateEngine


class TestWolfPyApplication:
    """Test core WolfPy application functionality."""
    
    def test_app_initialization(self):
        """Test basic app initialization."""
        app = WolfPy(debug=True)
        
        assert app.debug is True
        assert hasattr(app, 'router')
        assert hasattr(app, 'template_engine')
        assert app.static_folder == 'static'
        assert app.template_folder == 'templates'
    
    def test_app_with_custom_folders(self):
        """Test app initialization with custom folders."""
        app = WolfPy(
            template_folder='custom_templates',
            static_folder='custom_static'
        )
        
        assert app.template_folder == 'custom_templates'
        assert app.static_folder == 'custom_static'
    
    def test_route_registration(self):
        """Test route registration."""
        app = WolfPy()
        
        @app.route('/')
        def home(request):
            return "Home page"
        
        @app.route('/users/<int:user_id>')
        def user_detail(request, user_id):
            return f"User {user_id}"
        
        # Check that routes are registered
        assert len(app.router.routes) >= 2
        
        # Find our routes
        home_route = None
        user_route = None
        
        for route in app.router.routes:
            if route.path == '/' and route.method == 'GET':
                home_route = route
            elif '/users/' in route.path and route.method == 'GET':
                user_route = route
        
        assert home_route is not None
        assert user_route is not None
    
    def test_multiple_http_methods(self):
        """Test registering routes with multiple HTTP methods."""
        app = WolfPy()
        
        @app.route('/api/data', methods=['GET', 'POST'])
        def api_data(request):
            if request.method == 'GET':
                return "GET data"
            elif request.method == 'POST':
                return "POST data"
        
        # Should have registered 1 route with multiple methods
        api_routes = [
            route for route in app.router.routes
            if '/api/data' in route.path
        ]

        assert len(api_routes) == 1
        route = api_routes[0]
        assert 'GET' in route.methods
        assert 'POST' in route.methods


class TestRequestHandling:
    """Test request handling and parsing."""
    
    def test_request_creation(self):
        """Test creating Request objects."""
        environ = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/test',
            'QUERY_STRING': 'param=value',
            'CONTENT_TYPE': 'application/json',
            'HTTP_USER_AGENT': 'TestAgent/1.0',
            'wsgi.input': MagicMock()
        }
        
        request = Request(environ)
        
        assert request.method == 'GET'
        assert request.path == '/test'
        assert request.query_string == 'param=value'
        assert request.content_type == 'application/json'
        assert request.headers.get('User-Agent') == 'TestAgent/1.0'
    
    def test_request_args_parsing(self):
        """Test parsing query string arguments."""
        environ = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/search',
            'QUERY_STRING': 'q=python&category=programming&page=2',
            'wsgi.input': MagicMock()
        }

        request = Request(environ)

        # args returns lists (standard URL parsing behavior)
        assert request.args.get('q') == ['python']
        assert request.args.get('category') == ['programming']
        assert request.args.get('page') == ['2']
        assert request.args.get('nonexistent') is None

        # get_arg returns single values
        assert request.get_arg('q') == 'python'
        assert request.get_arg('category') == 'programming'
        assert request.get_arg('page') == '2'
        assert request.get_arg('nonexistent') is None
    
    def test_request_json_parsing(self):
        """Test parsing JSON request body."""
        import io
        import json

        json_data = {'name': 'test', 'value': 123}
        json_string = json.dumps(json_data)
        json_bytes = json_string.encode('utf-8')

        environ = {
            'REQUEST_METHOD': 'POST',
            'PATH_INFO': '/api/test',
            'CONTENT_TYPE': 'application/json',
            'CONTENT_LENGTH': str(len(json_bytes)),
            'wsgi.input': io.BytesIO(json_bytes)
        }

        request = Request(environ)
        parsed_json = request.get_json()

        assert parsed_json == json_data
        assert parsed_json['name'] == 'test'
        assert parsed_json['value'] == 123
    
    def test_request_form_parsing(self):
        """Test parsing form data."""
        import io
        from urllib.parse import urlencode

        form_data = {'username': 'testuser', 'password': 'secret'}
        form_string = urlencode(form_data)
        form_bytes = form_string.encode('utf-8')

        environ = {
            'REQUEST_METHOD': 'POST',
            'PATH_INFO': '/login',
            'CONTENT_TYPE': 'application/x-www-form-urlencoded',
            'CONTENT_LENGTH': str(len(form_bytes)),
            'wsgi.input': io.BytesIO(form_bytes)
        }

        request = Request(environ)

        # form returns lists (standard form parsing behavior)
        assert request.form.get('username') == ['testuser']
        assert request.form.get('password') == ['secret']

        # get_form returns single values
        assert request.get_form('username') == 'testuser'
        assert request.get_form('password') == 'secret'


class TestResponseHandling:
    """Test response creation and handling."""
    
    def test_basic_response(self):
        """Test creating basic responses."""
        response = Response("Hello, World!")

        assert response.body == "Hello, World!"
        assert response.status == 200
        assert response.headers.get('Content-Type') == "text/html; charset=utf-8"
    
    def test_response_with_status(self):
        """Test response with custom status code."""
        response = Response("Not Found", status=404)

        assert response.body == "Not Found"
        assert response.status == 404
    
    def test_json_response(self):
        """Test JSON response creation."""
        data = {'message': 'success', 'data': [1, 2, 3]}
        response = Response.json(data)

        assert response.status == 200
        assert response.headers.get('Content-Type') == "application/json; charset=utf-8"

        # Parse the JSON back to verify
        import json
        parsed = json.loads(response.body)
        assert parsed == data
    
    def test_redirect_response(self):
        """Test redirect response."""
        response = Response.redirect('/new-location')

        assert response.status == 302
        assert response.headers.get('Location') == '/new-location'

        # Test permanent redirect
        permanent_response = Response.redirect('/permanent', status=301)
        assert permanent_response.status == 301
    
    def test_error_responses(self):
        """Test error response helpers."""
        # 404 Not Found
        not_found = Response.not_found("Page not found")
        assert not_found.status == 404
        assert not_found.body == "Page not found"

        # 400 Bad Request
        bad_request = Response.bad_request("Invalid input")
        assert bad_request.status == 400
        assert bad_request.body == "Invalid input"

        # 401 Unauthorized
        unauthorized = Response.unauthorized("Login required")
        assert unauthorized.status == 401
        assert unauthorized.body == "Login required"

        # 403 Forbidden
        forbidden = Response.forbidden("Access denied")
        assert forbidden.status == 403
        assert forbidden.body == "Access denied"

        # 500 Internal Server Error
        server_error = Response.server_error("Something went wrong")
        assert server_error.status == 500
        assert server_error.body == "Something went wrong"
    
    def test_response_headers(self):
        """Test setting response headers."""
        response = Response("Test")
        response.headers['X-Custom-Header'] = 'custom-value'
        response.headers['Cache-Control'] = 'no-cache'
        
        assert response.headers.get('X-Custom-Header') == 'custom-value'
        assert response.headers.get('Cache-Control') == 'no-cache'
    
    def test_response_cookies(self):
        """Test setting response cookies."""
        response = Response("Test")
        response.set_cookie('session_id', 'abc123', max_age=3600)
        response.set_cookie('user_pref', 'dark_mode', secure=True, httponly=True)
        
        # Check that cookies are set (basic check)
        assert 'Set-Cookie' in response.headers


class RouteMatch:
    """Simple route match object for testing."""
    def __init__(self, handler, params):
        self.handler = handler
        self.params = params


class TestRouting:
    """Test routing functionality."""

    def test_router_initialization(self):
        """Test router initialization."""
        router = Router()
        assert router.routes == []
    
    def test_route_registration(self):
        """Test registering routes."""
        router = Router()

        def handler(request):
            return "Test"

        router.add_route('/', handler, ['GET'])
        router.add_route('/users/<int:id>', handler, ['GET'])

        assert len(router.routes) == 2

        # Check first route
        route1 = router.routes[0]
        assert route1.pattern == '/'
        assert 'GET' in route1.methods
        assert route1.handler == handler

        # Check second route
        route2 = router.routes[1]
        assert '/users/' in route2.pattern
        assert 'GET' in route2.methods
        assert route2.handler == handler
    
    def test_route_matching(self):
        """Test route matching."""
        router = Router()
        
        def home_handler(request):
            return "Home"
        
        def user_handler(request, user_id):
            return f"User {user_id}"
        
        router.add_route('/', home_handler, ['GET'])
        router.add_route('/users/<int:user_id>', user_handler, ['GET'])
        
        # Test exact match
        match = router.match('/', 'GET')
        assert match is not None
        assert match.handler == home_handler
        assert match.params == {}
        
        # Test parameterized match
        match = router.match('/users/123', 'GET')
        assert match is not None
        assert match.handler == user_handler
        assert match.params == {'user_id': 123}
        
        # Test no match
        match = router.match('/nonexistent', 'GET')
        assert match is None
    
    def test_route_parameters(self):
        """Test different route parameter types."""
        router = Router()
        
        def handler(request, **kwargs):
            return kwargs
        
        # Integer parameter
        router.add_route('/posts/<int:post_id>', handler, ['GET'])
        match = router.match('/posts/456', 'GET')
        assert match.params == {'post_id': 456}

        # String parameter
        router.add_route('/users/<str:username>', handler, ['GET'])
        match = router.match('/users/johndoe', 'GET')
        assert match.params == {'username': 'johndoe'}

        # Multiple parameters
        router.add_route('/posts/<int:post_id>/comments/<int:comment_id>', handler, ['GET'])
        match = router.match('/posts/123/comments/456', 'GET')
        assert match.params == {'post_id': 123, 'comment_id': 456}


class TestTemplateEngine:
    """Test template rendering functionality."""
    
    def setup_method(self):
        """Set up test template directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.template_engine = TemplateEngine(self.temp_dir)
        
        # Create test templates
        self.create_test_template('base.html', '''
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
</head>
<body>
    <h1>{{ heading }}</h1>
    <div>{{ content }}</div>
</body>
</html>
        ''')
        
        self.create_test_template('simple.html', '''
<h1>{{ message }}</h1>
<p>User: {{ user.name }}</p>
<ul>
{% for item in items %}
    <li>{{ item }}</li>
{% endfor %}
</ul>
        ''')
    
    def teardown_method(self):
        """Clean up test templates."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def create_test_template(self, filename, content):
        """Helper to create test template files."""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content.strip())
    
    def test_template_rendering(self):
        """Test basic template rendering."""
        context = {
            'title': 'Test Page',
            'heading': 'Welcome',
            'content': 'This is test content'
        }
        
        rendered = self.template_engine.render('base.html', context)
        
        assert 'Test Page' in rendered
        assert 'Welcome' in rendered
        assert 'This is test content' in rendered
        assert '<html>' in rendered
    
    def test_template_with_loops_and_objects(self):
        """Test template with loops and object access."""
        context = {
            'message': 'Hello World',
            'user': {'name': 'John Doe'},
            'items': ['Item 1', 'Item 2', 'Item 3']
        }
        
        rendered = self.template_engine.render('simple.html', context)
        
        assert 'Hello World' in rendered
        assert 'John Doe' in rendered
        assert 'Item 1' in rendered
        assert 'Item 2' in rendered
        assert 'Item 3' in rendered
    
    def test_template_not_found(self):
        """Test handling of missing templates."""
        with pytest.raises(FileNotFoundError):
            self.template_engine.render('nonexistent.html', {})


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
