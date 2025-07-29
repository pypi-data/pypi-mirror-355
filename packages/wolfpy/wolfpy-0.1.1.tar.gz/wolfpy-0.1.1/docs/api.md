# API Framework

![WolfPy API Framework](images/wolfpy-features.png)

WolfPy includes a powerful API framework for building RESTful web services. The API framework provides automatic JSON serialization, request validation, response formatting, and comprehensive documentation generation.

## 🚀 Quick Start

### Basic API Endpoint

```python
from wolfpy import WolfPy
from wolfpy.core.api_decorators import api_route, json_response

app = WolfPy(enable_api_framework=True)

@api_route('/api/users', methods=['GET'])
def get_users(request):
    users = [
        {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'},
        {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com'}
    ]
    return json_response(users)

@api_route('/api/users', methods=['POST'])
def create_user(request):
    # Automatic JSON parsing
    user_data = request.json
    
    # Create user (simplified)
    new_user = {
        'id': 3,
        'name': user_data['name'],
        'email': user_data['email']
    }
    
    return json_response(new_user, status=201)
```

## 🛠️ API Decorators

### Route Decorators

WolfPy provides convenient decorators for different HTTP methods:

```python
from wolfpy.core.api_decorators import (
    get_route, post_route, put_route, patch_route, delete_route
)

@get_route('/api/users/<int:user_id>')
def get_user(request, user_id):
    # Get user by ID
    return json_response({'id': user_id, 'name': 'User'})

@post_route('/api/users')
def create_user(request):
    # Create new user
    return json_response(request.json, status=201)

@put_route('/api/users/<int:user_id>')
def update_user(request, user_id):
    # Update user
    return json_response({'id': user_id, 'updated': True})

@delete_route('/api/users/<int:user_id>')
def delete_user(request, user_id):
    # Delete user
    return json_response({'deleted': True}, status=204)
```

### Response Helpers

```python
from wolfpy.core.api_decorators import json_response

# Success response
return json_response({'message': 'Success'})

# Error response
return json_response({'error': 'Not found'}, status=404)

# Paginated response
return json_response({
    'data': items,
    'pagination': {
        'page': 1,
        'per_page': 10,
        'total': 100
    }
})
```

## 🔍 Request Validation

### Required Fields Validation

```python
from wolfpy.core.api_decorators import validate_required_fields

@post_route('/api/users')
@validate_required_fields(['name', 'email'])
def create_user(request):
    # Fields are automatically validated
    return json_response(request.json, status=201)
```

### Custom Validation

```python
def validate_email(email):
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@post_route('/api/users')
def create_user(request):
    data = request.json
    
    # Custom validation
    if not validate_email(data.get('email', '')):
        return json_response({'error': 'Invalid email'}, status=400)
    
    return json_response(data, status=201)
```

## 📊 API Router

Organize your API endpoints with APIRouter:

```python
from wolfpy.core.api_decorators import APIRouter

# Create API router
api = APIRouter(prefix='/api/v1')

@api.get('/users')
def list_users(request):
    return json_response([])

@api.post('/users')
def create_user(request):
    return json_response(request.json, status=201)

@api.get('/users/<int:user_id>')
def get_user(request, user_id):
    return json_response({'id': user_id})

# Register router with app
app.include_router(api)
```

## 🔐 Authentication & Authorization

### API Key Authentication

```python
def require_api_key(func):
    def wrapper(request, *args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or not validate_api_key(api_key):
            return json_response({'error': 'Invalid API key'}, status=401)
        return func(request, *args, **kwargs)
    return wrapper

@get_route('/api/protected')
@require_api_key
def protected_endpoint(request):
    return json_response({'message': 'Access granted'})
```

### JWT Authentication

```python
import jwt

def require_jwt(func):
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return json_response({'error': 'Missing token'}, status=401)
        
        token = auth_header[7:]  # Remove 'Bearer '
        try:
            payload = jwt.decode(token, app.secret_key, algorithms=['HS256'])
            request.user_id = payload['user_id']
        except jwt.InvalidTokenError:
            return json_response({'error': 'Invalid token'}, status=401)
        
        return func(request, *args, **kwargs)
    return wrapper

@get_route('/api/profile')
@require_jwt
def get_profile(request):
    return json_response({'user_id': request.user_id})
```

## 📄 API Documentation

### Automatic Documentation

WolfPy can generate API documentation automatically:

```python
# Enable API documentation
app = WolfPy(enable_api_framework=True)

# Documentation available at /api/docs
# OpenAPI spec available at /api/openapi.json
```

### Custom Documentation

```python
@api_route('/api/users', methods=['GET'])
def get_users(request):
    """
    Get all users
    
    Returns:
        List of user objects
    
    Example:
        GET /api/users
        
        Response:
        [
            {"id": 1, "name": "John", "email": "john@example.com"}
        ]
    """
    return json_response([])
```

## 🔄 Pagination

### Built-in Pagination

```python
from wolfpy.core.api_decorators import paginate_data

@get_route('/api/users')
def get_users(request):
    # Get all users
    all_users = User.all()
    
    # Paginate results
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    return paginate_data(all_users, page, per_page)
```

### Custom Pagination

```python
@get_route('/api/posts')
def get_posts(request):
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 10)), 100)  # Max 100
    
    offset = (page - 1) * per_page
    posts = Post.limit(per_page).offset(offset).all()
    total = Post.count()
    
    return json_response({
        'data': [post.to_dict() for post in posts],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    })
```

## 🚦 Rate Limiting

```python
from functools import wraps
import time

# Simple rate limiter
rate_limit_store = {}

def rate_limit(max_requests=100, window=3600):
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            client_ip = request.environ.get('REMOTE_ADDR', 'unknown')
            current_time = time.time()
            
            # Clean old entries
            rate_limit_store[client_ip] = [
                req_time for req_time in rate_limit_store.get(client_ip, [])
                if current_time - req_time < window
            ]
            
            # Check rate limit
            if len(rate_limit_store.get(client_ip, [])) >= max_requests:
                return json_response({
                    'error': 'Rate limit exceeded'
                }, status=429)
            
            # Record request
            rate_limit_store.setdefault(client_ip, []).append(current_time)
            
            return func(request, *args, **kwargs)
        return wrapper
    return decorator

@get_route('/api/data')
@rate_limit(max_requests=10, window=60)  # 10 requests per minute
def get_data(request):
    return json_response({'data': 'value'})
```

## 🧪 Testing APIs

```python
import pytest
from wolfpy.testing import TestClient

def test_api_endpoints():
    client = TestClient(app)
    
    # Test GET endpoint
    response = client.get('/api/users')
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    
    # Test POST endpoint
    user_data = {'name': 'Test User', 'email': 'test@example.com'}
    response = client.post('/api/users', json=user_data)
    assert response.status_code == 201
    assert response.json()['name'] == 'Test User'
    
    # Test error handling
    response = client.post('/api/users', json={})
    assert response.status_code == 400

def test_authentication():
    client = TestClient(app)
    
    # Test without authentication
    response = client.get('/api/protected')
    assert response.status_code == 401
    
    # Test with authentication
    headers = {'X-API-Key': 'valid-key'}
    response = client.get('/api/protected', headers=headers)
    assert response.status_code == 200
```

## 🔧 Configuration

```python
# API configuration
app = WolfPy(
    enable_api_framework=True,
    api_prefix='/api',
    api_version='v1',
    debug=True
)

# Custom API settings
app.api.configure({
    'title': 'My API',
    'version': '1.0.0',
    'description': 'My awesome API',
    'contact': {
        'name': 'API Support',
        'email': 'support@example.com'
    }
})
```

## 📈 Best Practices

### 1. Consistent Response Format

```python
def api_response(data=None, message=None, status=200):
    response_data = {
        'success': status < 400,
        'message': message,
        'data': data
    }
    return json_response(response_data, status=status)

@get_route('/api/users')
def get_users(request):
    users = User.all()
    return api_response(
        data=[user.to_dict() for user in users],
        message='Users retrieved successfully'
    )
```

### 2. Error Handling

```python
@api_route('/api/users/<int:user_id>')
def get_user(request, user_id):
    try:
        user = User.find(user_id)
        if not user:
            return api_response(
                message='User not found',
                status=404
            )
        return api_response(data=user.to_dict())
    except Exception as e:
        return api_response(
            message='Internal server error',
            status=500
        )
```

### 3. Input Validation

```python
from marshmallow import Schema, fields, ValidationError

class UserSchema(Schema):
    name = fields.Str(required=True, validate=lambda x: len(x) > 0)
    email = fields.Email(required=True)
    age = fields.Int(validate=lambda x: x >= 0)

@post_route('/api/users')
def create_user(request):
    schema = UserSchema()
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return api_response(
            message='Validation error',
            data=err.messages,
            status=400
        )
    
    user = User.create(**data)
    return api_response(
        data=user.to_dict(),
        message='User created successfully',
        status=201
    )
```

The WolfPy API framework provides everything you need to build robust, scalable APIs with minimal boilerplate code. 🚀
