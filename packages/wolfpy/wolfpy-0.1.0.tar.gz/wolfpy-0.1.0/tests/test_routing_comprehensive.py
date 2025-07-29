"""
Comprehensive unit tests for WolfPy Routing System.

This test suite covers all aspects of routing including:
- Route registration and matching
- Parameter extraction and type conversion
- Route constraints and validation
- HTTP method handling
- Route groups and prefixes
- Dynamic route generation
- Route caching and optimization
- Error handling in routing
"""

import pytest
from unittest.mock import MagicMock

from src.wolfpy.core.routing import Router, Route, RouteGroup
from src.wolfpy.core.request import Request
from src.wolfpy.core.response import Response


class TestRouteBasics:
    """Test basic route functionality."""
    
    def test_route_creation(self):
        """Test creating a basic route."""
        def handler():
            return "Hello World"
        
        route = Route('/hello', handler, methods=['GET'])
        
        assert route.pattern == '/hello'
        assert route.handler == handler
        assert route.methods == ['GET']
        assert route.name is None
    
    def test_route_with_name(self):
        """Test creating a named route."""
        def handler():
            return "Hello World"
        
        route = Route('/hello', handler, methods=['GET'], name='hello')
        
        assert route.name == 'hello'
    
    def test_route_with_constraints(self):
        """Test creating a route with parameter constraints."""
        def handler(user_id):
            return f"User {user_id}"
        
        constraints = {'user_id': r'\d+'}
        route = Route('/user/<user_id>', handler, methods=['GET'], constraints=constraints)
        
        assert route.constraints == constraints


class TestRouterBasics:
    """Test basic router functionality."""
    
    def test_router_initialization(self):
        """Test router initialization."""
        router = Router()
        
        assert router.routes == []
        assert router.route_cache == {}
        assert router.enable_caching is True
    
    def test_add_route(self):
        """Test adding a route to the router."""
        router = Router()
        
        def handler():
            return "Hello"
        
        router.add_route('/hello', handler, methods=['GET'])
        
        assert len(router.routes) == 1
        assert router.routes[0].pattern == '/hello'
        assert router.routes[0].handler == handler
    
    def test_route_decorator(self):
        """Test using route decorator."""
        router = Router()
        
        @router.route('/hello', methods=['GET'])
        def hello():
            return "Hello World"
        
        assert len(router.routes) == 1
        assert router.routes[0].pattern == '/hello'
        assert router.routes[0].handler == hello


class TestRouteMatching:
    """Test route matching functionality."""
    
    def test_exact_match(self):
        """Test exact route matching."""
        router = Router()
        
        def handler():
            return "Hello"
        
        router.add_route('/hello', handler, methods=['GET'])
        
        # Create mock request
        environ = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/hello'
        }
        request = Request(environ)
        
        match = router.match(request)
        
        assert match is not None
        assert match['handler'] == handler
        assert match['params'] == {}
    
    def test_no_match(self):
        """Test when no route matches."""
        router = Router()
        
        def handler():
            return "Hello"
        
        router.add_route('/hello', handler, methods=['GET'])
        
        # Create mock request for different path
        environ = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/goodbye'
        }
        request = Request(environ)
        
        match = router.match(request)
        
        assert match is None
    
    def test_method_mismatch(self):
        """Test when path matches but method doesn't."""
        router = Router()
        
        def handler():
            return "Hello"
        
        router.add_route('/hello', handler, methods=['GET'])
        
        # Create mock request with different method
        environ = {
            'REQUEST_METHOD': 'POST',
            'PATH_INFO': '/hello'
        }
        request = Request(environ)
        
        match = router.match(request)
        
        assert match is None


class TestParameterExtraction:
    """Test parameter extraction from routes."""
    
    def test_simple_parameter(self):
        """Test extracting a simple parameter."""
        router = Router()
        
        def handler(name):
            return f"Hello {name}"
        
        router.add_route('/hello/<name>', handler, methods=['GET'])
        
        environ = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/hello/world'
        }
        request = Request(environ)
        
        match = router.match(request)
        
        assert match is not None
        assert match['params'] == {'name': 'world'}
    
    def test_multiple_parameters(self):
        """Test extracting multiple parameters."""
        router = Router()
        
        def handler(category, item_id):
            return f"Category: {category}, Item: {item_id}"
        
        router.add_route('/category/<category>/item/<item_id>', handler, methods=['GET'])
        
        environ = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/category/electronics/item/123'
        }
        request = Request(environ)
        
        match = router.match(request)
        
        assert match is not None
        assert match['params'] == {'category': 'electronics', 'item_id': '123'}
    
    def test_parameter_with_constraint(self):
        """Test parameter extraction with constraints."""
        router = Router()
        
        def handler(user_id):
            return f"User {user_id}"
        
        constraints = {'user_id': r'\d+'}
        router.add_route('/user/<user_id>', handler, methods=['GET'], constraints=constraints)
        
        # Test valid parameter
        environ = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/user/123'
        }
        request = Request(environ)
        
        match = router.match(request)
        
        assert match is not None
        assert match['params'] == {'user_id': '123'}
        
        # Test invalid parameter
        environ = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/user/abc'
        }
        request = Request(environ)
        
        match = router.match(request)
        
        assert match is None
    
    def test_optional_parameter(self):
        """Test optional parameters."""
        router = Router()
        
        def handler(page=1):
            return f"Page {page}"
        
        router.add_route('/posts', handler, methods=['GET'])
        router.add_route('/posts/<page>', handler, methods=['GET'], constraints={'page': r'\d+'})
        
        # Test without parameter
        environ = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/posts'
        }
        request = Request(environ)
        
        match = router.match(request)
        
        assert match is not None
        assert match['params'] == {}
        
        # Test with parameter
        environ = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/posts/2'
        }
        request = Request(environ)
        
        match = router.match(request)
        
        assert match is not None
        assert match['params'] == {'page': '2'}


class TestRouteGroups:
    """Test route group functionality."""
    
    def test_route_group_creation(self):
        """Test creating a route group."""
        group = RouteGroup('/api')
        
        assert group.prefix == '/api'
        assert group.routes == []
    
    def test_route_group_add_route(self):
        """Test adding routes to a group."""
        group = RouteGroup('/api')
        
        def handler():
            return "API Response"
        
        group.add_route('/users', handler, methods=['GET'])
        
        assert len(group.routes) == 1
        assert group.routes[0].pattern == '/users'  # Prefix not applied yet
    
    def test_route_group_registration(self):
        """Test registering a route group with router."""
        router = Router()
        group = RouteGroup('/api')
        
        def users_handler():
            return "Users"
        
        def posts_handler():
            return "Posts"
        
        group.add_route('/users', users_handler, methods=['GET'])
        group.add_route('/posts', posts_handler, methods=['GET'])
        
        router.register_group(group)
        
        assert len(router.routes) == 2
        
        # Test that routes have correct prefixed patterns
        patterns = [route.pattern for route in router.routes]
        assert '/api/users' in patterns
        assert '/api/posts' in patterns


class TestRouteConstraints:
    """Test route constraint functionality."""
    
    def test_integer_constraint(self):
        """Test integer parameter constraint."""
        router = Router()
        
        def handler(user_id):
            return f"User {user_id}"
        
        constraints = {'user_id': r'\d+'}
        router.add_route('/user/<user_id>', handler, methods=['GET'], constraints=constraints)
        
        # Valid integer
        environ = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/user/123'
        }
        request = Request(environ)
        match = router.match(request)
        assert match is not None
        
        # Invalid (non-integer)
        environ = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/user/abc'
        }
        request = Request(environ)
        match = router.match(request)
        assert match is None
    
    def test_slug_constraint(self):
        """Test slug parameter constraint."""
        router = Router()
        
        def handler(slug):
            return f"Post: {slug}"
        
        constraints = {'slug': r'[a-z0-9-]+'}
        router.add_route('/post/<slug>', handler, methods=['GET'], constraints=constraints)
        
        # Valid slug
        environ = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/post/my-awesome-post'
        }
        request = Request(environ)
        match = router.match(request)
        assert match is not None
        
        # Invalid slug (contains uppercase)
        environ = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/post/My-Awesome-Post'
        }
        request = Request(environ)
        match = router.match(request)
        assert match is None
    
    def test_multiple_constraints(self):
        """Test multiple parameter constraints."""
        router = Router()
        
        def handler(year, month, day):
            return f"Date: {year}-{month}-{day}"
        
        constraints = {
            'year': r'\d{4}',
            'month': r'(0[1-9]|1[0-2])',
            'day': r'(0[1-9]|[12][0-9]|3[01])'
        }
        router.add_route('/date/<year>/<month>/<day>', handler, methods=['GET'], constraints=constraints)
        
        # Valid date
        environ = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/date/2023/12/25'
        }
        request = Request(environ)
        match = router.match(request)
        assert match is not None
        assert match['params'] == {'year': '2023', 'month': '12', 'day': '25'}
        
        # Invalid month
        environ = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/date/2023/13/25'
        }
        request = Request(environ)
        match = router.match(request)
        assert match is None


class TestRouteCaching:
    """Test route caching functionality."""
    
    def test_route_caching_enabled(self):
        """Test that route caching works when enabled."""
        router = Router(enable_caching=True)
        
        def handler():
            return "Hello"
        
        router.add_route('/hello', handler, methods=['GET'])
        
        environ = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/hello'
        }
        request = Request(environ)
        
        # First match should populate cache
        match1 = router.match(request)
        assert match1 is not None
        assert len(router.route_cache) == 1
        
        # Second match should use cache
        match2 = router.match(request)
        assert match2 is not None
        assert match1 == match2
    
    def test_route_caching_disabled(self):
        """Test that route caching can be disabled."""
        router = Router(enable_caching=False)
        
        def handler():
            return "Hello"
        
        router.add_route('/hello', handler, methods=['GET'])
        
        environ = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/hello'
        }
        request = Request(environ)
        
        # Match should not populate cache
        match = router.match(request)
        assert match is not None
        assert len(router.route_cache) == 0


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
