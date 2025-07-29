#!/usr/bin/env python3
"""
WolfPy REST API Example

A complete REST API demonstrating:
- RESTful endpoints with proper HTTP methods
- JSON request/response handling
- API authentication with tokens
- Request validation
- Error handling
- API documentation
"""

import os
import sys
import json
import hashlib
import secrets
from pathlib import Path
from datetime import datetime, timedelta

# Add WolfPy to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from wolfpy import WolfPy
from wolfpy.core.response import Response
from wolfpy.core.database import Model
from wolfpy.core.api_decorators import api_route, json_response


# Database Models
class User(Model):
    """User model for API authentication."""
    table_name = 'users'
    fields = {
        'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
        'username': 'TEXT UNIQUE NOT NULL',
        'email': 'TEXT UNIQUE NOT NULL',
        'password_hash': 'TEXT NOT NULL',
        'api_token': 'TEXT UNIQUE',
        'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
    }


class Task(Model):
    """Task model for todo API."""
    table_name = 'tasks'
    fields = {
        'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
        'title': 'TEXT NOT NULL',
        'description': 'TEXT',
        'completed': 'BOOLEAN DEFAULT FALSE',
        'user_id': 'INTEGER NOT NULL',
        'due_date': 'TIMESTAMP',
        'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
    }


# Create WolfPy application
app = WolfPy(
    debug=True,
    database_url='sqlite:///api.db',
    enable_api_framework=True
)


# Authentication helpers
def generate_api_token():
    """Generate a secure API token."""
    return secrets.token_urlsafe(32)


def hash_password(password: str) -> str:
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate_token(request):
    """Authenticate request using API token."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header[7:]  # Remove 'Bearer '
    user = User.where('api_token = ?', [token])
    return user[0] if user else None


def require_auth(func):
    """Decorator to require authentication."""
    def wrapper(request, *args, **kwargs):
        user = authenticate_token(request)
        if not user:
            return json_response({'error': 'Authentication required'}, status=401)
        request.user = user
        return func(request, *args, **kwargs)
    return wrapper


def validate_json(required_fields):
    """Decorator to validate JSON request data."""
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            if not request.is_json():
                return json_response({'error': 'JSON data required'}, status=400)
            
            data = request.json
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                return json_response({
                    'error': 'Missing required fields',
                    'missing_fields': missing_fields
                }, status=400)
            
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


# API Routes

# Authentication endpoints
@api_route('/api/auth/register', methods=['POST'])
@validate_json(['username', 'email', 'password'])
def register(request):
    """Register a new user."""
    data = request.json
    
    # Check if user already exists
    existing_user = User.where('username = ? OR email = ?', [data['username'], data['email']])
    if existing_user:
        return json_response({'error': 'Username or email already exists'}, status=400)
    
    # Create new user
    api_token = generate_api_token()
    user = User.create(
        username=data['username'],
        email=data['email'],
        password_hash=hash_password(data['password']),
        api_token=api_token
    )
    
    return json_response({
        'message': 'User created successfully',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        },
        'api_token': api_token
    }, status=201)


@api_route('/api/auth/login', methods=['POST'])
@validate_json(['username', 'password'])
def login(request):
    """Login user and return API token."""
    data = request.json
    
    user = User.where('username = ?', [data['username']])
    if not user or user[0].password_hash != hash_password(data['password']):
        return json_response({'error': 'Invalid credentials'}, status=401)
    
    user = user[0]
    
    # Generate new API token
    user.api_token = generate_api_token()
    user.save()
    
    return json_response({
        'message': 'Login successful',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        },
        'api_token': user.api_token
    })


# Task endpoints
@api_route('/api/tasks', methods=['GET'])
@require_auth
def list_tasks(request):
    """Get all tasks for authenticated user."""
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 10)), 100)
    completed = request.args.get('completed')
    
    # Build query
    query = 'user_id = ?'
    params = [request.user.id]
    
    if completed is not None:
        query += ' AND completed = ?'
        params.append(completed.lower() == 'true')
    
    # Get tasks with pagination
    offset = (page - 1) * per_page
    tasks = Task.where(query, params, limit=per_page, offset=offset)
    total = len(Task.where(query, params))
    
    return json_response({
        'tasks': [task.to_dict() for task in tasks],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    })


@api_route('/api/tasks', methods=['POST'])
@require_auth
@validate_json(['title'])
def create_task(request):
    """Create a new task."""
    data = request.json
    
    task = Task.create(
        title=data['title'],
        description=data.get('description', ''),
        user_id=request.user.id,
        due_date=data.get('due_date')
    )
    
    return json_response({
        'message': 'Task created successfully',
        'task': task.to_dict()
    }, status=201)


@api_route('/api/tasks/<int:task_id>', methods=['GET'])
@require_auth
def get_task(request, task_id):
    """Get a specific task."""
    task = Task.find(task_id)
    
    if not task or task.user_id != request.user.id:
        return json_response({'error': 'Task not found'}, status=404)
    
    return json_response({'task': task.to_dict()})


@api_route('/api/tasks/<int:task_id>', methods=['PUT'])
@require_auth
def update_task(request, task_id):
    """Update a specific task."""
    task = Task.find(task_id)
    
    if not task or task.user_id != request.user.id:
        return json_response({'error': 'Task not found'}, status=404)
    
    if not request.is_json():
        return json_response({'error': 'JSON data required'}, status=400)
    
    data = request.json
    
    # Update task fields
    if 'title' in data:
        task.title = data['title']
    if 'description' in data:
        task.description = data['description']
    if 'completed' in data:
        task.completed = bool(data['completed'])
    if 'due_date' in data:
        task.due_date = data['due_date']
    
    task.updated_at = datetime.now()
    task.save()
    
    return json_response({
        'message': 'Task updated successfully',
        'task': task.to_dict()
    })


@api_route('/api/tasks/<int:task_id>', methods=['DELETE'])
@require_auth
def delete_task(request, task_id):
    """Delete a specific task."""
    task = Task.find(task_id)
    
    if not task or task.user_id != request.user.id:
        return json_response({'error': 'Task not found'}, status=404)
    
    task.delete()
    
    return json_response({'message': 'Task deleted successfully'}, status=204)


# Statistics endpoint
@api_route('/api/stats', methods=['GET'])
@require_auth
def get_stats(request):
    """Get user statistics."""
    total_tasks = len(Task.where('user_id = ?', [request.user.id]))
    completed_tasks = len(Task.where('user_id = ? AND completed = ?', [request.user.id, True]))
    pending_tasks = total_tasks - completed_tasks
    
    return json_response({
        'stats': {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'completion_rate': round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 2)
        }
    })


# API documentation endpoint
@app.route('/api/docs')
def api_docs(request):
    """API documentation."""
    docs = {
        'title': 'WolfPy Todo API',
        'version': '1.0.0',
        'description': 'A simple todo API built with WolfPy',
        'base_url': 'http://localhost:8000/api',
        'authentication': 'Bearer token in Authorization header',
        'endpoints': {
            'POST /auth/register': 'Register a new user',
            'POST /auth/login': 'Login and get API token',
            'GET /tasks': 'List user tasks (with pagination)',
            'POST /tasks': 'Create a new task',
            'GET /tasks/{id}': 'Get specific task',
            'PUT /tasks/{id}': 'Update specific task',
            'DELETE /tasks/{id}': 'Delete specific task',
            'GET /stats': 'Get user statistics'
        }
    }
    
    return json_response(docs)


# Health check endpoint
@api_route('/api/health', methods=['GET'])
def health_check(request):
    """Health check endpoint."""
    return json_response({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })


# Initialize database
def init_database():
    """Initialize database with tables."""
    app.database.create_tables([User, Task])
    print("Database initialized")


if __name__ == '__main__':
    init_database()
    print("🚀 WolfPy Todo API starting...")
    print("📖 API docs: http://localhost:8000/api/docs")
    print("🏥 Health check: http://localhost:8000/api/health")
    print("\n📝 Example usage:")
    print("1. Register: POST /api/auth/register")
    print("2. Login: POST /api/auth/login")
    print("3. Use token in Authorization header: Bearer <token>")
    app.run(host='0.0.0.0', port=8000)
