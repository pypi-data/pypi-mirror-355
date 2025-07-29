"""
Integration Tests for WolfPy Framework.

This test suite covers end-to-end integration testing including:
- Full application workflows
- Authentication + API integration
- Database + API integration
- Template rendering with authentication
- Complete request/response cycles
"""

import pytest
import tempfile
import os
import json
from unittest.mock import MagicMock, patch

from src.wolfpy import WolfPy
from src.wolfpy.core.auth import Auth, PasswordPolicy
from src.wolfpy.core.database import Database, Model, IntegerField, StringField, EmailField, BooleanField
from src.wolfpy.core.api import APIFramework, APIModel, APIField
from src.wolfpy.core.request import Request
from src.wolfpy.core.response import Response


class TestFullApplicationIntegration:
    """Test complete application integration scenarios."""
    
    def setup_method(self):
        """Set up complete test application."""
        # Create temporary database
        self.db_file = tempfile.mktemp(suffix='.db')
        
        # Create WolfPy app with all features
        self.app = WolfPy(debug=True)
        
        # Setup authentication
        self.app.auth = Auth(
            secret_key='integration-test-secret',
            use_jwt=True,
            password_policy=PasswordPolicy(min_length=6)
        )
        
        # Setup database
        self.app.db = Database(self.db_file)
        
        # Define models
        class User(Model):
            id = IntegerField(primary_key=True)
            username = StringField(max_length=50, unique=True)
            email = EmailField()
            is_active = BooleanField(default=True)
        
        class Post(Model):
            id = IntegerField(primary_key=True)
            title = StringField(max_length=200)
            content = StringField(max_length=1000)
            author_id = StringField(max_length=50)
        
        self.User = User
        self.Post = Post
        
        # Create tables
        self.app.db.create_tables(User, Post)
        
        # Setup API
        self.api = APIFramework(
            self.app,
            enable_rate_limiting=True,
            enable_versioning=True
        )
        
        # Create test user
        self.test_user = self.app.auth.create_user_profile(
            username='testuser',
            password='TestPass123!',
            email='test@example.com'
        )
        
        self.setup_routes()
    
    def teardown_method(self):
        """Clean up test environment."""
        # Close database connection first
        if hasattr(self, 'app') and hasattr(self.app, 'db') and self.app.db:
            self.app.db.close()

        # Then remove file with retry logic for Windows
        if os.path.exists(self.db_file):
            try:
                os.unlink(self.db_file)
            except PermissionError:
                # On Windows, sometimes the file is still locked
                import time
                time.sleep(0.1)
                try:
                    os.unlink(self.db_file)
                except PermissionError:
                    pass  # Ignore if still can't delete
    
    def setup_routes(self):
        """Set up test routes."""
        from src.wolfpy.core.auth import login_required
        
        # Basic routes
        @self.app.route('/')
        def home(request):
            return Response("Welcome to WolfPy!")
        
        @self.app.route('/login', methods=['POST'])
        def login(request):
            data = request.get_json()
            user = self.app.auth.authenticate(
                data['username'], 
                data['password'],
                request
            )
            
            if user:
                tokens = self.app.auth.login_user(user)
                return Response.json({
                    'success': True,
                    'tokens': tokens,
                    'user': {'id': user.id, 'username': user.username}
                })
            else:
                return Response.json({'error': 'Invalid credentials'}, status=401)
        
        @self.app.route('/protected')
        @login_required(self.app.auth)
        def protected(request):
            return Response.json({
                'message': 'This is protected content',
                'user': request.user.username
            })
        
        # API routes
        @self.api.get('/users')
        @login_required(self.app.auth)
        def get_users(request):
            users = self.User.objects.all(self.app.db)
            return [{'id': u.id, 'username': u.username} for u in users]
        
        @self.api.post('/posts')
        @login_required(self.app.auth)
        def create_post(request):
            data = request.get_json()
            post = self.Post(
                title=data['title'],
                content=data['content'],
                author_id=str(request.user.id)
            )
            post.save(self.app.db)

            return Response.json({
                'id': post.id,
                'title': post.title,
                'content': post.content,
                'author_id': post.author_id
            }, status=201)
    
    def create_mock_request(self, method='GET', path='/', headers=None, 
                           body=None, query_string=''):
        """Create a mock WSGI request."""
        import io
        
        environ = {
            'REQUEST_METHOD': method,
            'PATH_INFO': path,
            'QUERY_STRING': query_string,
            'CONTENT_TYPE': 'application/json',
            'CONTENT_LENGTH': str(len(body or '')),
            'wsgi.input': io.StringIO(body or ''),
            'HTTP_HOST': 'localhost:8000',
            'HTTP_USER_AGENT': 'TestClient/1.0'
        }
        
        if headers:
            for key, value in headers.items():
                environ[f'HTTP_{key.upper().replace("-", "_")}'] = value
        
        return Request(environ)
    
    def test_basic_request_response_cycle(self):
        """Test basic request/response handling."""
        request = self.create_mock_request('GET', '/')
        
        # Find and execute route
        match = self.app.router.match('/', 'GET')
        assert match is not None
        
        response = match.handler(request)
        assert isinstance(response, Response)
        assert response.body == "Welcome to WolfPy!"
        assert response.status_code == 200
    
    def test_authentication_workflow(self):
        """Test complete authentication workflow."""
        # Test login
        login_data = {
            'username': 'testuser',
            'password': 'TestPass123!'
        }
        
        request = self.create_mock_request(
            'POST', 
            '/login',
            body=json.dumps(login_data)
        )
        
        # Find and execute login route
        match = self.app.router.match('/login', 'POST')
        assert match is not None
        
        response = match.handler(request)
        assert isinstance(response, Response)
        assert response.status_code == 200
        
        # Parse response
        response_data = json.loads(response.body)
        assert response_data['success'] is True
        assert 'tokens' in response_data
        assert 'access_token' in response_data['tokens']
        
        # Test accessing protected route with token
        access_token = response_data['tokens']['access_token']
        
        protected_request = self.create_mock_request(
            'GET',
            '/protected',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        # Mock the app reference for auth
        protected_request._app = self.app
        
        # Find and execute protected route
        match = self.app.router.match('/protected', 'GET')
        assert match is not None
        
        response = match.handler(protected_request)
        assert isinstance(response, Response)
        assert response.status_code == 200
        
        response_data = json.loads(response.body)
        assert 'This is protected content' in response_data['message']
    
    def test_database_api_integration(self):
        """Test database operations through API."""
        # First authenticate
        login_data = {
            'username': 'testuser',
            'password': 'TestPass123!'
        }
        
        login_request = self.create_mock_request(
            'POST',
            '/login',
            body=json.dumps(login_data)
        )
        
        login_match = self.app.router.match('/login', 'POST')
        login_response = login_match.handler(login_request)
        login_data = json.loads(login_response.body)
        access_token = login_data['tokens']['access_token']
        
        # Create a post via API
        post_data = {
            'title': 'Test Post',
            'content': 'This is a test post content'
        }
        
        create_request = self.create_mock_request(
            'POST',
            '/api/v1/posts',
            headers={'Authorization': f'Bearer {access_token}'},
            body=json.dumps(post_data)
        )
        create_request._app = self.app
        
        # Find and execute create post route
        match = self.app.router.match('/api/v1/posts', 'POST')
        assert match is not None
        
        response = match.handler(create_request)
        assert isinstance(response, Response)
        assert response.status_code == 201
        
        # Parse response
        response_data = json.loads(response.body)
        assert response_data['title'] == 'Test Post'
        assert response_data['content'] == 'This is a test post content'
        assert response_data['id'] is not None
        
        # Verify post was saved to database
        saved_post = self.Post.objects.get(self.app.db, id=response_data['id'])
        assert saved_post.title == 'Test Post'
        assert saved_post.author_id == str(self.test_user.id)
    
    def test_api_users_endpoint(self):
        """Test API users endpoint with authentication."""
        # Create additional test user in database
        db_user = self.User(
            username='dbuser',
            email='dbuser@example.com',
            is_active=True
        )
        db_user.save(self.app.db)
        
        # Authenticate
        login_data = {
            'username': 'testuser',
            'password': 'TestPass123!'
        }
        
        login_request = self.create_mock_request(
            'POST',
            '/login',
            body=json.dumps(login_data)
        )
        
        login_match = self.app.router.match('/login', 'POST')
        login_response = login_match.handler(login_request)
        login_data = json.loads(login_response.body)
        access_token = login_data['tokens']['access_token']
        
        # Get users via API
        users_request = self.create_mock_request(
            'GET',
            '/api/v1/users',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        users_request._app = self.app
        
        # Find and execute users route
        match = self.app.router.match('/api/v1/users', 'GET')
        assert match is not None
        
        response = match.handler(users_request)
        assert isinstance(response, Response)
        assert response.status_code == 200
        
        # Parse response
        response_data = json.loads(response.body)

        # Handle both direct list and wrapped response formats
        if isinstance(response_data, dict) and 'result' in response_data:
            # API framework wrapped the response
            users_list = response_data['result']
        else:
            # Direct list response
            users_list = response_data

        assert isinstance(users_list, list)
        assert len(users_list) >= 1

        # Check that our test user is in the list
        usernames = [user['username'] for user in users_list]
        assert 'dbuser' in usernames
    
    def test_unauthenticated_access_denied(self):
        """Test that protected routes deny unauthenticated access."""
        # Try to access protected route without token
        request = self.create_mock_request('GET', '/protected')
        request._app = self.app
        
        match = self.app.router.match('/protected', 'GET')
        response = match.handler(request)
        
        assert isinstance(response, Response)
        assert response.status_code in [401, 302]  # Unauthorized or redirect
    
    def test_invalid_credentials(self):
        """Test login with invalid credentials."""
        login_data = {
            'username': 'testuser',
            'password': 'WrongPassword'
        }
        
        request = self.create_mock_request(
            'POST',
            '/login',
            body=json.dumps(login_data)
        )
        
        match = self.app.router.match('/login', 'POST')
        response = match.handler(request)
        
        assert isinstance(response, Response)
        assert response.status_code == 401
        
        response_data = json.loads(response.body)
        assert 'error' in response_data
        assert 'Invalid credentials' in response_data['error']
    
    def test_route_not_found(self):
        """Test handling of non-existent routes."""
        match = self.app.router.match('/nonexistent', 'GET')
        assert match is None
    
    def test_method_not_allowed(self):
        """Test handling of wrong HTTP methods."""
        # Try POST on a GET-only route
        match = self.app.router.match('/', 'POST')
        assert match is None  # Should not match
        
        # The home route only accepts GET
        get_match = self.app.router.match('/', 'GET')
        assert get_match is not None


class TestErrorHandlingIntegration:
    """Test error handling in integrated scenarios."""
    
    def setup_method(self):
        """Set up test app with error scenarios."""
        self.app = WolfPy(debug=True)
        
        @self.app.route('/error')
        def error_route(request):
            raise Exception("Test error")
        
        @self.app.route('/json-error')
        def json_error_route(request):
            # Try to parse invalid JSON
            return request.get_json()
    
    def create_mock_request(self, method='GET', path='/', body=None):
        """Create a mock request."""
        import io
        
        environ = {
            'REQUEST_METHOD': method,
            'PATH_INFO': path,
            'QUERY_STRING': '',
            'CONTENT_TYPE': 'application/json',
            'CONTENT_LENGTH': str(len(body or '')),
            'wsgi.input': io.StringIO(body or ''),
        }
        
        return Request(environ)
    
    def test_exception_handling(self):
        """Test that exceptions are properly handled."""
        request = self.create_mock_request('GET', '/error')
        
        match = self.app.router.match('/error', 'GET')
        assert match is not None
        
        # In a real app, this would be caught by error handling middleware
        with pytest.raises(Exception):
            match.handler(request)
    
    def test_invalid_json_handling(self):
        """Test handling of invalid JSON."""
        request = self.create_mock_request(
            'POST',
            '/json-error',
            body='invalid json{'
        )
        
        match = self.app.router.match('/json-error', 'GET')
        if match:
            # Should handle JSON parsing error gracefully
            try:
                response = match.handler(request)
                # If it returns a response, it should indicate an error
                if isinstance(response, Response):
                    assert response.status_code >= 400
            except (ValueError, json.JSONDecodeError):
                # This is expected for invalid JSON
                pass


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
