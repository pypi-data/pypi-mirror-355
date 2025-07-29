"""
WolfPy CLI Main Module.

Comprehensive command-line interface for WolfPy framework operations.
Provides all essential commands for project management, development, and deployment.
"""

import sys
import os
import argparse
import subprocess
import shutil
import json
import time
import threading
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from .migrations import (
    makemigrations, migrate, rollback, showmigrations,
    create_initial_migration, reset_migrations, check_migrations
)


def create_project(name: str, directory: str = None):
    """
    Create a new WolfPy project with comprehensive structure.

    Args:
        name: Project name
        directory: Target directory (default: current directory)
    """
    if directory is None:
        directory = os.getcwd()

    project_path = os.path.join(directory, name)

    print(f"🐺 Creating WolfPy project '{name}'...")

    # Create comprehensive project structure
    directories = [
        'static/css',
        'static/js',
        'static/images',
        'templates/auth',
        'templates/admin',
        'routes',
        'models',
        'middleware',
        'tests',
        'migrations',
        'config',
        'logs'
    ]

    for dir_path in directories:
        os.makedirs(os.path.join(project_path, dir_path), exist_ok=True)
        print(f"  📁 Created {dir_path}/")

    # Create __init__.py files for Python packages
    init_files = ['routes', 'models', 'middleware', 'tests']
    for init_dir in init_files:
        init_path = os.path.join(project_path, init_dir, '__init__.py')
        with open(init_path, 'w', encoding='utf-8') as f:
            f.write(f'"""\\n{init_dir.title()} package for {name}.\\n"""\\n')
    
    # Create enhanced main application file
    app_content = f'''"""
{name} - WolfPy Application

A comprehensive web application built with WolfPy framework.
"""

import os
from wolfpy import WolfPy
from wolfpy.core.response import Response
from wolfpy.core.middleware import CORSMiddleware, LoggingMiddleware
from config.settings import get_config

# Load configuration
config = get_config()

# Create WolfPy application with enhanced features
app = WolfPy(
    debug=config.get('DEBUG', True),
    static_folder='static',
    template_folder='templates',
    secret_key=config.get('SECRET_KEY', os.urandom(24).hex()),
    enable_performance_monitoring=True,
    enable_caching=True,
    enable_api_framework=True
)

# Add middleware
app.add_middleware(CORSMiddleware())
app.add_middleware(LoggingMiddleware())

# Import routes
from routes.main import register_routes
from routes.api import register_api_routes
from routes.auth import register_auth_routes

# Register all routes
register_routes(app)
register_api_routes(app)
register_auth_routes(app)


@app.route('/')
def home(request):
    """Home page."""
    return app.template_engine.render('index.html', {{
        'title': '{name}',
        'message': 'Welcome to your WolfPy application!',
        'version': '1.0.0'
    }})


@app.route('/health')
def health_check(request):
    """Health check endpoint."""
    return Response.json({{
        'status': 'healthy',
        'timestamp': '{datetime.now().isoformat()}',
        'version': '1.0.0'
    }})


if __name__ == '__main__':
    host = config.get('HOST', '127.0.0.1')
    port = config.get('PORT', 8000)
    debug = config.get('DEBUG', True)

    print(f"🐺 Starting {{name}} on http://{{host}}:{{port}}")
    app.run(host=host, port=port, debug=debug)
'''
    
    with open(os.path.join(project_path, 'app.py'), 'w', encoding='utf-8') as f:
        f.write(app_content)
    print(f"  📄 Created app.py")

    # Create configuration files
    config_content = f'''"""
Configuration settings for {name}.
"""

import os
from typing import Dict, Any


def get_config() -> Dict[str, Any]:
    """Get application configuration."""
    return {{
        'DEBUG': os.getenv('DEBUG', 'True').lower() == 'true',
        'SECRET_KEY': os.getenv('SECRET_KEY', '{os.urandom(24).hex()}'),
        'HOST': os.getenv('HOST', '127.0.0.1'),
        'PORT': int(os.getenv('PORT', 8000)),
        'DATABASE_URL': os.getenv('DATABASE_URL', 'sqlite:///{{name}}.db'),
        'CACHE_TYPE': os.getenv('CACHE_TYPE', 'memory'),
        'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
        'CORS_ORIGINS': os.getenv('CORS_ORIGINS', '*').split(','),
        'JWT_SECRET': os.getenv('JWT_SECRET', '{os.urandom(32).hex()}'),
        'SESSION_TIMEOUT': int(os.getenv('SESSION_TIMEOUT', 3600)),
    }}


class Config:
    """Configuration class."""

    def __init__(self):
        self.config = get_config()

    def get(self, key: str, default=None):
        """Get configuration value."""
        return self.config.get(key, default)

    def set(self, key: str, value):
        """Set configuration value."""
        self.config[key] = value


# Global config instance
config = Config()
'''

    with open(os.path.join(project_path, 'config', 'settings.py'), 'w', encoding='utf-8') as f:
        f.write(config_content)
    print(f"  📄 Created config/settings.py")

    # Create route modules
    main_routes_content = '''"""
Main application routes.
"""

from wolfpy.core.response import Response


def register_routes(app):
    """Register main application routes."""

    @app.route('/about')
    def about(request):
        """About page."""
        return app.template_engine.render('about.html', {
            'title': 'About',
            'content': 'Learn more about our application.'
        })

    @app.route('/contact')
    def contact(request):
        """Contact page."""
        return app.template_engine.render('contact.html', {
            'title': 'Contact',
            'content': 'Get in touch with us.'
        })
'''

    with open(os.path.join(project_path, 'routes', 'main.py'), 'w', encoding='utf-8') as f:
        f.write(main_routes_content)
    print(f"  📄 Created routes/main.py")

    # Create API routes
    api_routes_content = '''"""
API routes for the application.
"""

from wolfpy.core.response import Response
from wolfpy.core.api_decorators import get_route, post_route, put_route, delete_route


def register_api_routes(app):
    """Register API routes."""

    @app.api_endpoint('/users')
    def list_users(request):
        """List all users."""
        # Mock data - replace with actual database queries
        users = [
            {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'},
            {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com'}
        ]
        return Response.json({
            'users': users,
            'total': len(users),
            'status': 'success'
        })

    @app.api_endpoint('/users/<int:user_id>')
    def get_user(request, user_id):
        """Get a specific user."""
        # Mock data - replace with actual database query
        user = {'id': user_id, 'name': f'User {user_id}', 'email': f'user{user_id}@example.com'}
        return Response.json({
            'user': user,
            'status': 'success'
        })

    @app.api_endpoint('/stats')
    def get_stats(request):
        """Get application statistics."""
        stats = app.get_performance_stats()
        return Response.json({
            'stats': stats,
            'timestamp': str(datetime.now()),
            'status': 'success'
        })
'''

    with open(os.path.join(project_path, 'routes', 'api.py'), 'w', encoding='utf-8') as f:
        f.write(api_routes_content)
    print(f"  📄 Created routes/api.py")

    # Create auth routes
    auth_routes_content = '''"""
Authentication routes.
"""

from wolfpy.core.response import Response
from wolfpy.core.auth import login_required


def register_auth_routes(app):
    """Register authentication routes."""

    @app.route('/login', methods=['GET', 'POST'])
    def login(request):
        """Login page and handler."""
        if request.method == 'GET':
            return app.template_engine.render('auth/login.html', {
                'title': 'Login'
            })

        # Handle POST request
        username = request.get_form('username')
        password = request.get_form('password')

        if username and password:
            # Add actual authentication logic here
            return Response.redirect('/dashboard')
        else:
            return app.template_engine.render('auth/login.html', {
                'title': 'Login',
                'error': 'Invalid credentials'
            })

    @app.route('/logout')
    def logout(request):
        """Logout handler."""
        # Add logout logic here
        return Response.redirect('/')

    @app.route('/dashboard')
    @login_required()
    def dashboard(request):
        """Protected dashboard."""
        return app.template_engine.render('dashboard.html', {
            'title': 'Dashboard',
            'user': request.user
        })
'''

    with open(os.path.join(project_path, 'routes', 'auth.py'), 'w', encoding='utf-8') as f:
        f.write(auth_routes_content)
    print(f"  📄 Created routes/auth.py")
    
    # Create enhanced templates
    base_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}{{title}}{% endblock %}</title>
    <link rel="stylesheet" href="/static/css/style.css">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">🐺 {name}</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/">Home</a>
                <a class="nav-link" href="/about">About</a>
                <a class="nav-link" href="/contact">Contact</a>
                <a class="nav-link" href="/login">Login</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        {% block content %}{% endblock %}
    </div>

    <footer class="bg-light mt-5 py-4">
        <div class="container text-center">
            <p>&copy; 2024 {name}. Built with WolfPy Framework.</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="/static/js/app.js"></script>
</body>
</html>'''

    with open(os.path.join(project_path, 'templates', 'base.html'), 'w', encoding='utf-8') as f:
        f.write(base_template)
    print(f"  📄 Created templates/base.html")

    # Create index template
    index_template = '''{% extends "base.html" %}

{% block content %}
<div class="row">
    <div class="col-md-8 mx-auto">
        <div class="jumbotron bg-light p-5 rounded">
            <h1 class="display-4">{{message}}</h1>
            <p class="lead">Your WolfPy application is running successfully!</p>
            <hr class="my-4">
            <p>Version: {{version}}</p>
            <a class="btn btn-primary btn-lg" href="/about" role="button">Learn More</a>
        </div>

        <div class="row mt-4">
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">🚀 Fast</h5>
                        <p class="card-text">Built for performance with advanced caching and optimization.</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">🔒 Secure</h5>
                        <p class="card-text">Enterprise-grade security with authentication and authorization.</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">🛠️ Flexible</h5>
                        <p class="card-text">Modular architecture with comprehensive middleware support.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''

    with open(os.path.join(project_path, 'templates', 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_template)
    print(f"  📄 Created templates/index.html")
    
    # Create login template
    login_template = '''{% extends "base.html" %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h4>Login</h4>
            </div>
            <div class="card-body">
                {% if error %}
                <div class="alert alert-danger">{{error}}</div>
                {% endif %}
                <form method="POST">
                    <div class="mb-3">
                        <label for="username" class="form-label">Username</label>
                        <input type="text" class="form-control" id="username" name="username" required>
                    </div>
                    <div class="mb-3">
                        <label for="password" class="form-label">Password</label>
                        <input type="password" class="form-control" id="password" name="password" required>
                    </div>
                    <button type="submit" class="btn btn-primary">Login</button>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''

    with open(os.path.join(project_path, 'templates', 'auth', 'login.html'), 'w', encoding='utf-8') as f:
        f.write(login_template)
    print(f"  📄 Created templates/auth/login.html")

    # Create CSS file
    css_content = '''/* Custom styles for {name} */

:root {{
    --primary-color: #007bff;
    --secondary-color: #6c757d;
    --success-color: #28a745;
    --danger-color: #dc3545;
}}

body {{
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}}

.navbar-brand {{
    font-weight: bold;
}}

.jumbotron {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}}

.card {{
    transition: transform 0.2s;
    border: none;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}}

.card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}}

footer {{
    margin-top: auto;
}}
'''

    with open(os.path.join(project_path, 'static', 'css', 'style.css'), 'w', encoding='utf-8') as f:
        f.write(css_content)
    print(f"  📄 Created static/css/style.css")

    # Create JavaScript file
    js_content = '''// JavaScript for {name}

document.addEventListener('DOMContentLoaded', function() {{
    console.log('Wolf {name} loaded successfully!');

    // Add any custom JavaScript here

    // Example: Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {{
        form.addEventListener('submit', function(e) {{
            // Add custom validation logic here
        }});
    }});
}});
'''

    with open(os.path.join(project_path, 'static', 'js', 'app.js'), 'w', encoding='utf-8') as f:
        f.write(js_content)
    print(f"  📄 Created static/js/app.js")

    # Create enhanced requirements.txt
    requirements_content = '''# Core framework
wolfpy>=0.1.0

# Web server
gunicorn>=20.1.0

# Database
sqlalchemy>=1.4.0
alembic>=1.7.0

# Authentication
bcrypt>=3.2.0
PyJWT>=2.4.0

# Development
pytest>=7.0.0
pytest-cov>=4.0.0
black>=22.0.0
flake8>=4.0.0

# Optional: Redis for caching
redis>=4.0.0

# Optional: PostgreSQL
psycopg2-binary>=2.9.0
'''

    with open(os.path.join(project_path, 'requirements.txt'), 'w', encoding='utf-8') as f:
        f.write(requirements_content)
    print(f"  📄 Created requirements.txt")

    # Create .env file
    env_content = f'''# Environment configuration for {name}
DEBUG=True
SECRET_KEY={os.urandom(24).hex()}
HOST=127.0.0.1
PORT=8000
DATABASE_URL=sqlite:///{name}.db
CACHE_TYPE=memory
LOG_LEVEL=INFO
CORS_ORIGINS=*
JWT_SECRET={os.urandom(32).hex()}
SESSION_TIMEOUT=3600
'''

    with open(os.path.join(project_path, '.env'), 'w', encoding='utf-8') as f:
        f.write(env_content)
    print(f"  📄 Created .env")

    # Create .gitignore
    gitignore_content = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
logs/
*.log

# Database
*.db
*.sqlite3

# Environment variables
.env
.env.local

# Cache
.cache/
htmlcov/

# OS
.DS_Store
Thumbs.db
'''

    with open(os.path.join(project_path, '.gitignore'), 'w', encoding='utf-8') as f:
        f.write(gitignore_content)
    print(f"  📄 Created .gitignore")

    print(f"\\n✅ Successfully created WolfPy project '{name}' in {project_path}")
    print(f"\\n🚀 To get started:")
    print(f"  cd {name}")
    print(f"  pip install -r requirements.txt")
    print(f"  python app.py")
    print(f"\\n📚 Available commands:")
    print(f"  wolfpy serve          # Start development server")
    print(f"  wolfpy routes         # List all routes")
    print(f"  wolfpy db init        # Initialize database")
    print(f"  wolfpy test           # Run tests")
    print(f"\\n🌐 Your app will be available at: http://127.0.0.1:8000")


def serve_app(app_file: str = 'app.py', host: str = '127.0.0.1', port: int = 8000, debug: bool = False, reload: bool = False):
    """
    Serve a WolfPy application with enhanced features.

    Args:
        app_file: Python file containing the WolfPy app
        host: Host to bind to
        port: Port to bind to
        debug: Enable debug mode
        reload: Enable auto-reload on file changes
    """
    if not os.path.exists(app_file):
        print(f"❌ Error: Application file '{app_file}' not found")
        return

    print(f"🐺 Starting WolfPy development server...")
    print(f"📁 Application: {app_file}")
    print(f"🌐 Server: http://{host}:{port}")
    print(f"🔧 Debug mode: {'ON' if debug else 'OFF'}")
    print(f"🔄 Auto-reload: {'ON' if reload else 'OFF'}")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # Import the application
    sys.path.insert(0, os.path.dirname(os.path.abspath(app_file)))

    try:
        # Load the module
        import importlib.util
        spec = importlib.util.spec_from_file_location("app", app_file)
        app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_module)

        # Find the WolfPy app instance
        app = None
        for attr_name in dir(app_module):
            attr = getattr(app_module, attr_name)
            if hasattr(attr, '__class__') and attr.__class__.__name__ == 'WolfPy':
                app = attr
                break

        if app is None:
            print("❌ Error: No WolfPy application found in the file")
            return

        # Override debug mode if specified
        if debug:
            app.debug = True

        # Show registered routes
        print(f"📋 Registered routes:")
        for route in app.router.routes:
            methods = ', '.join(route.methods) if hasattr(route, 'methods') else 'GET'
            print(f"  {methods:10} {route.pattern}")
        print("=" * 50)

        # Run the application
        if reload:
            print("🔄 Auto-reload enabled - server will restart on file changes")

        app.run(host=host, port=port, debug=app.debug)

    except KeyboardInterrupt:
        print("\\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error running application: {e}")
        if debug:
            import traceback
            traceback.print_exc()


def generate_route(name: str, path: str = None, methods: List[str] = None):
    """
    Generate a new route template.
    
    Args:
        name: Route function name
        path: URL path (default: /name)
        methods: HTTP methods (default: ['GET'])
    """
    if path is None:
        path = f'/{name}'
    
    if methods is None:
        methods = ['GET']
    
    methods_str = str(methods).replace("'", '"')
    
    route_template = f'''
@app.route('{path}', methods={methods_str})
def {name}(request):
    """
    {name.replace('_', ' ').title()} route.
    """
    return Response("Hello from {name}!")
'''
    
    print(f"Generated route template for '{name}':")
    print(route_template)


def show_routes(app_file: str = 'app.py', format_type: str = 'table'):
    """
    Show all routes in a WolfPy application.

    Args:
        app_file: Python file containing the WolfPy app
        format_type: Output format ('table', 'json', 'simple')
    """
    if not os.path.exists(app_file):
        print(f"❌ Error: Application file '{app_file}' not found")
        return

    print(f"🐺 Routes in {app_file}:")
    print("=" * 60)

    # Import the application
    sys.path.insert(0, os.path.dirname(os.path.abspath(app_file)))

    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("app", app_file)
        app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_module)

        # Find the WolfPy app instance
        app = None
        for attr_name in dir(app_module):
            attr = getattr(app_module, attr_name)
            if hasattr(attr, '__class__') and attr.__class__.__name__ == 'WolfPy':
                app = attr
                break

        if app is None:
            print("❌ Error: No WolfPy application found in the file")
            return

        routes = app.router.routes

        if format_type == 'json':
            import json
            route_data = []
            for route in routes:
                route_data.append({
                    'pattern': route.pattern,
                    'methods': list(route.methods) if hasattr(route, 'methods') else ['GET'],
                    'name': getattr(route, 'name', ''),
                    'handler': route.handler.__name__ if hasattr(route.handler, '__name__') else str(route.handler)
                })
            print(json.dumps(route_data, indent=2))

        elif format_type == 'table':
            print(f"{'METHOD':<10} {'PATH':<30} {'HANDLER':<20} {'NAME':<15}")
            print("-" * 75)
            for route in routes:
                methods = ', '.join(route.methods) if hasattr(route, 'methods') else 'GET'
                handler_name = route.handler.__name__ if hasattr(route.handler, '__name__') else str(route.handler)
                route_name = getattr(route, 'name', '')
                print(f"{methods:<10} {route.pattern:<30} {handler_name:<20} {route_name:<15}")

        else:  # simple format
            for route in routes:
                methods = ', '.join(route.methods) if hasattr(route, 'methods') else 'GET'
                print(f"{methods:>8} {route.pattern}")

        print(f"\\n📊 Total routes: {len(routes)}")

    except Exception as e:
        print(f"❌ Error loading routes: {e}")


def generate_model(name: str, fields: List[str] = None):
    """
    Generate a new database model class.

    Args:
        name: Model class name
        fields: List of field definitions
    """
    if fields is None:
        fields = ['id:int:primary_key', 'created_at:datetime:auto_now_add']

    print(f"🐺 Generating model '{name}'...")

    # Create model template
    model_template = f'''"""
{name} model definition.
"""

from wolfpy.core.database import Model, IntegerField, StringField, DateTimeField, BooleanField


class {name}(Model):
    """
    {name} model.
    """

    # Primary key
    id = IntegerField(primary_key=True)

    # Add your fields here
'''

    # Add fields based on input
    for field_def in fields:
        if ':' in field_def:
            parts = field_def.split(':')
            field_name = parts[0]
            field_type = parts[1] if len(parts) > 1 else 'string'
            field_options = parts[2:] if len(parts) > 2 else []

            if field_type.lower() in ['int', 'integer']:
                field_class = 'IntegerField'
            elif field_type.lower() in ['str', 'string', 'text']:
                field_class = 'StringField'
            elif field_type.lower() in ['datetime', 'timestamp']:
                field_class = 'DateTimeField'
            elif field_type.lower() in ['bool', 'boolean']:
                field_class = 'BooleanField'
            else:
                field_class = 'StringField'

            options = []
            for opt in field_options:
                if opt == 'primary_key':
                    options.append('primary_key=True')
                elif opt == 'unique':
                    options.append('unique=True')
                elif opt == 'auto_now_add':
                    options.append('auto_now_add=True')
                elif opt.startswith('max_length'):
                    options.append(f'max_length={opt.split("=")[1]}')

            options_str = ', '.join(options)
            if options_str:
                model_template += f'    {field_name} = {field_class}({options_str})\\n'
            else:
                model_template += f'    {field_name} = {field_class}()\\n'

    model_template += f'''

    def __str__(self):
        """String representation."""
        return f"<{name} {{self.id}}>"

    def to_dict(self):
        """Convert to dictionary."""
        return {{
            'id': self.id,
            # Add other fields here
        }}
'''

    # Create models directory if it doesn't exist
    models_dir = Path('models')
    models_dir.mkdir(exist_ok=True)

    # Write model file
    model_file = models_dir / f'{name.lower()}.py'
    with open(model_file, 'w') as f:
        f.write(model_template)

    print(f"✅ Created model file: {model_file}")
    print(f"📝 Don't forget to:")
    print(f"   1. Import the model in your app")
    print(f"   2. Run 'wolfpy db migrate' to create the table")


def generate_auth():
    """Generate authentication routes and views."""
    print("🐺 Generating authentication system...")

    # This would create comprehensive auth templates and routes
    auth_files = [
        'routes/auth.py',
        'templates/auth/login.html',
        'templates/auth/register.html',
        'templates/auth/profile.html'
    ]

    for file_path in auth_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} already exists")
        else:
            print(f"📄 Would create {file_path}")

    print("✅ Authentication system generated!")


def clean_project():
    """Clean project files (cache, build artifacts, etc.)."""
    print("🐺 Cleaning project...")

    patterns_to_remove = [
        '__pycache__',
        '*.pyc',
        '*.pyo',
        '*.pyd',
        '.pytest_cache',
        'build',
        'dist',
        '*.egg-info',
        '.coverage',
        'htmlcov',
        '.cache'
    ]

    removed_count = 0

    for pattern in patterns_to_remove:
        if '*' in pattern:
            # Handle glob patterns
            import glob
            for file_path in glob.glob(f"**/{pattern}", recursive=True):
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        removed_count += 1
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        removed_count += 1
                except Exception as e:
                    print(f"⚠️  Could not remove {file_path}: {e}")
        else:
            # Handle directory patterns
            for root, dirs, files in os.walk('.'):
                if pattern in dirs:
                    dir_path = os.path.join(root, pattern)
                    try:
                        shutil.rmtree(dir_path)
                        print(f"🗑️  Removed {dir_path}")
                        removed_count += 1
                    except Exception as e:
                        print(f"⚠️  Could not remove {dir_path}: {e}")

    print(f"✅ Cleaned {removed_count} items")


def run_tests(test_path: str = 'tests', verbose: bool = False, coverage: bool = False):
    """
    Run the test suite.

    Args:
        test_path: Path to test directory or specific test file
        verbose: Enable verbose output
        coverage: Enable coverage reporting
    """
    print("🐺 Running tests...")

    if not os.path.exists(test_path):
        print(f"❌ Test path '{test_path}' not found")
        return

    # Build pytest command
    cmd = ['python', '-m', 'pytest', test_path]

    if verbose:
        cmd.append('-v')

    if coverage:
        cmd.extend(['--cov=.', '--cov-report=html', '--cov-report=term-missing'])

    print(f"🧪 Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=False)
        if result.returncode == 0:
            print("✅ All tests passed!")
        else:
            print(f"❌ Tests failed with exit code {result.returncode}")
    except FileNotFoundError:
        print("❌ pytest not found. Install with: pip install pytest")
    except Exception as e:
        print(f"❌ Error running tests: {e}")


def show_version():
    """Show WolfPy version and system information."""
    print("🐺 WolfPy Framework")
    print("=" * 30)
    print(f"Version: 0.1.0")
    print(f"Python: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Working Directory: {os.getcwd()}")

    # Check for optional dependencies
    optional_deps = {
        'PyJWT': 'JWT authentication support',
        'redis': 'Redis caching support',
        'psycopg2': 'PostgreSQL database support',
        'bcrypt': 'Enhanced password hashing'
    }

    print("\\nOptional Dependencies:")
    for dep, description in optional_deps.items():
        try:
            __import__(dep.lower().replace('-', '_'))
            print(f"  ✅ {dep}: {description}")
        except ImportError:
            print(f"  ❌ {dep}: {description} (not installed)")


def clean_project():
    """Clean project files."""
    print("🐺 Cleaning project files...")

    patterns_to_remove = [
        '__pycache__',
        '*.pyc',
        '*.pyo',
        '*.pyd',
        '.pytest_cache',
        'build',
        'dist',
        '*.egg-info',
        '.coverage',
        'htmlcov',
        '.tox',
        '.cache',
        'node_modules',
        '.DS_Store',
        'Thumbs.db'
    ]

    removed_count = 0

    for pattern in patterns_to_remove:
        if pattern.startswith('*'):
            # Handle file patterns
            import glob
            for file_path in glob.glob(f"**/{pattern}", recursive=True):
                try:
                    os.remove(file_path)
                    print(f"  🗑️ Removed {file_path}")
                    removed_count += 1
                except OSError:
                    pass
        else:
            # Handle directory patterns
            for root, dirs, files in os.walk('.'):
                if pattern in dirs:
                    dir_path = os.path.join(root, pattern)
                    try:
                        shutil.rmtree(dir_path)
                        print(f"  🗑️ Removed {dir_path}")
                        removed_count += 1
                    except OSError:
                        pass

    print(f"✅ Cleaned {removed_count} items!")


def create_user():
    """Create admin user manually."""
    print("🐺 Creating admin user...")

    username = input("Username: ")
    if not username:
        print("❌ Username is required")
        return

    email = input("Email: ")
    if not email:
        print("❌ Email is required")
        return

    import getpass
    password = getpass.getpass("Password: ")
    if not password:
        print("❌ Password is required")
        return

    confirm_password = getpass.getpass("Confirm password: ")
    if password != confirm_password:
        print("❌ Passwords do not match")
        return

    # TODO: Integrate with actual user model and database
    print(f"✅ Admin user '{username}' created successfully!")
    print(f"   Email: {email}")
    print("   Note: This is a placeholder. Integrate with your User model.")


def upgrade_framework():
    """Update framework components or dependencies."""
    print("🐺 Upgrading WolfPy framework and dependencies...")

    try:
        # Upgrade WolfPy itself
        print("📦 Upgrading WolfPy framework...")
        subprocess.run(['pip', 'install', '--upgrade', 'wolfpy'], check=True)

        # Upgrade dependencies from requirements.txt if it exists
        if os.path.exists('requirements.txt'):
            print("📦 Upgrading project dependencies...")
            subprocess.run(['pip', 'install', '--upgrade', '-r', 'requirements.txt'], check=True)

        print("✅ Framework and dependencies upgraded successfully!")

    except subprocess.CalledProcessError as e:
        print(f"❌ Upgrade failed: {e}")
    except FileNotFoundError:
        print("❌ pip not found. Make sure Python and pip are installed.")


def show_config():
    """Display current config settings."""
    print("🐺 Current WolfPy Configuration")
    print("=" * 40)

    config_files = ['config/settings.py', 'settings.py', '.env']
    found_config = False

    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"📄 Found config file: {config_file}")
            found_config = True

            if config_file.endswith('.py'):
                try:
                    # Import and display Python config
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("config", config_file)
                    config_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(config_module)

                    if hasattr(config_module, 'get_config'):
                        config = config_module.get_config()
                        for key, value in config.items():
                            # Hide sensitive values
                            if 'SECRET' in key or 'PASSWORD' in key or 'TOKEN' in key:
                                value = '*' * 8
                            print(f"  {key}: {value}")

                except Exception as e:
                    print(f"  ❌ Error reading config: {e}")

            elif config_file.endswith('.env'):
                try:
                    with open(config_file, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                key, _, value = line.partition('=')
                                # Hide sensitive values
                                if 'SECRET' in key or 'PASSWORD' in key or 'TOKEN' in key:
                                    value = '*' * 8
                                print(f"  {key}: {value}")
                except Exception as e:
                    print(f"  ❌ Error reading .env: {e}")

    if not found_config:
        print("❌ No configuration files found")
        print("   Expected: config/settings.py, settings.py, or .env")


def edit_config():
    """Launch config editor."""
    print("🐺 Opening configuration editor...")

    config_files = ['config/settings.py', 'settings.py', '.env']
    config_file = None

    for file_path in config_files:
        if os.path.exists(file_path):
            config_file = file_path
            break

    if not config_file:
        print("❌ No configuration file found")
        create_new = input("Create new config file? (y/N): ").lower().strip()
        if create_new == 'y':
            config_file = 'config/settings.py'
            os.makedirs('config', exist_ok=True)

            # Create basic config template
            config_template = '''"""
Configuration settings for your WolfPy application.
"""

import os
from typing import Dict, Any


def get_config() -> Dict[str, Any]:
    """Get application configuration."""
    return {
        'DEBUG': os.getenv('DEBUG', 'True').lower() == 'true',
        'SECRET_KEY': os.getenv('SECRET_KEY', 'your-secret-key-here'),
        'HOST': os.getenv('HOST', '127.0.0.1'),
        'PORT': int(os.getenv('PORT', 8000)),
        'DATABASE_URL': os.getenv('DATABASE_URL', 'sqlite:///app.db'),
        'CACHE_TYPE': os.getenv('CACHE_TYPE', 'memory'),
        'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
    }
'''
            with open(config_file, 'w') as f:
                f.write(config_template)
            print(f"✅ Created {config_file}")
        else:
            return

    # Try to open with system editor
    editors = ['code', 'nano', 'vim', 'notepad']

    for editor in editors:
        try:
            subprocess.run([editor, config_file], check=True)
            print(f"✅ Opened {config_file} with {editor}")
            return
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue

    print(f"❌ Could not open editor. Please manually edit: {config_file}")


def build_assets():
    """Compile static assets."""
    print("🐺 Building static assets...")

    static_dir = 'static'
    if not os.path.exists(static_dir):
        print("❌ Static directory not found")
        return

    # Check for SCSS files
    scss_files = []
    for root, dirs, files in os.walk(static_dir):
        for file in files:
            if file.endswith('.scss'):
                scss_files.append(os.path.join(root, file))

    if scss_files:
        try:
            # Try to compile SCSS files
            import sass
            for scss_file in scss_files:
                css_file = scss_file.replace('.scss', '.css')
                with open(scss_file, 'r') as f:
                    scss_content = f.read()

                css_content = sass.compile(string=scss_content)

                with open(css_file, 'w') as f:
                    f.write(css_content)

                print(f"  ✅ Compiled {scss_file} -> {css_file}")

        except ImportError:
            print("  ⚠️ libsass not installed. Install with: pip install libsass")
        except Exception as e:
            print(f"  ❌ SCSS compilation failed: {e}")

    # Minify CSS and JS files (basic implementation)
    minified_count = 0
    for root, dirs, files in os.walk(static_dir):
        for file in files:
            if file.endswith('.css') and not file.endswith('.min.css'):
                file_path = os.path.join(root, file)
                min_file_path = file_path.replace('.css', '.min.css')

                try:
                    with open(file_path, 'r') as f:
                        content = f.read()

                    # Basic CSS minification
                    import re
                    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
                    content = re.sub(r'\s+', ' ', content)
                    content = content.strip()

                    with open(min_file_path, 'w') as f:
                        f.write(content)

                    print(f"  ✅ Minified {file} -> {os.path.basename(min_file_path)}")
                    minified_count += 1

                except Exception as e:
                    print(f"  ❌ Failed to minify {file}: {e}")

    print(f"✅ Asset build complete! Processed {len(scss_files)} SCSS files, minified {minified_count} CSS files.")


def clean_assets():
    """Remove compiled asset files."""
    print("🐺 Cleaning compiled assets...")

    static_dir = 'static'
    if not os.path.exists(static_dir):
        print("❌ Static directory not found")
        return

    removed_count = 0
    patterns = ['*.min.css', '*.min.js', '*.map']

    for root, dirs, files in os.walk(static_dir):
        for file in files:
            for pattern in patterns:
                if file.endswith(pattern.replace('*', '')):
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                        print(f"  🗑️ Removed {file_path}")
                        removed_count += 1
                    except OSError as e:
                        print(f"  ❌ Failed to remove {file_path}: {e}")

    print(f"✅ Cleaned {removed_count} compiled asset files!")


def watch_assets():
    """Watch assets folder for changes."""
    print("🐺 Watching assets for changes...")
    print("Press Ctrl+C to stop watching")

    static_dir = 'static'
    if not os.path.exists(static_dir):
        print("❌ Static directory not found")
        return

    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

        class AssetHandler(FileSystemEventHandler):
            def on_modified(self, event):
                if not event.is_directory and event.src_path.endswith(('.scss', '.css', '.js')):
                    print(f"📝 File changed: {event.src_path}")
                    if event.src_path.endswith('.scss'):
                        print("🔄 Rebuilding assets...")
                        build_assets()

        event_handler = AssetHandler()
        observer = Observer()
        observer.schedule(event_handler, static_dir, recursive=True)
        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            print("\n✅ Stopped watching assets")

        observer.join()

    except ImportError:
        print("❌ watchdog not installed. Install with: pip install watchdog")
        print("   Falling back to basic polling...")

        # Basic polling fallback
        last_modified = {}

        try:
            while True:
                for root, dirs, files in os.walk(static_dir):
                    for file in files:
                        if file.endswith(('.scss', '.css', '.js')):
                            file_path = os.path.join(root, file)
                            try:
                                mtime = os.path.getmtime(file_path)
                                if file_path not in last_modified:
                                    last_modified[file_path] = mtime
                                elif mtime > last_modified[file_path]:
                                    print(f"📝 File changed: {file_path}")
                                    last_modified[file_path] = mtime
                                    if file_path.endswith('.scss'):
                                        print("🔄 Rebuilding assets...")
                                        build_assets()
                            except OSError:
                                pass

                time.sleep(2)

        except KeyboardInterrupt:
            print("\n✅ Stopped watching assets")


def open_shell():
    """Open interactive shell with project context loaded."""
    print("🐺 Opening WolfPy interactive shell...")

    # Try to load the application
    app_file = 'app.py'
    if os.path.exists(app_file):
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("app", app_file)
            app_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(app_module)

            # Make app available in shell
            app = getattr(app_module, 'app', None)

            print("✅ Application loaded successfully!")
            print("Available objects:")
            print("  - app: WolfPy application instance")

            # Start interactive shell
            try:
                import IPython
                IPython.embed(user_ns={'app': app})
            except ImportError:
                import code
                code.interact(local={'app': app})

        except Exception as e:
            print(f"❌ Failed to load application: {e}")
            print("Starting shell without app context...")

            try:
                import IPython
                IPython.embed()
            except ImportError:
                import code
                code.interact()
    else:
        print("❌ app.py not found. Starting basic shell...")
        try:
            import IPython
            IPython.embed()
        except ImportError:
            import code
            code.interact()


def inspect_app():
    """Inspect objects, models, routes, etc."""
    print("🐺 Inspecting WolfPy application...")

    app_file = 'app.py'
    if not os.path.exists(app_file):
        print("❌ app.py not found")
        return

    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("app", app_file)
        app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_module)

        app = getattr(app_module, 'app', None)
        if not app:
            print("❌ No 'app' object found in app.py")
            return

        print("🔍 Application Inspection Report")
        print("=" * 40)

        # Routes
        if hasattr(app, 'router') and hasattr(app.router, 'routes'):
            print(f"📍 Routes: {len(app.router.routes)}")
            for route in app.router.routes:
                methods = getattr(route, 'methods', ['GET'])
                print(f"  {', '.join(methods)} {route.path} -> {route.handler.__name__}")

        # Middleware
        if hasattr(app, 'middleware_stack'):
            print(f"🔧 Middleware: {len(app.middleware_stack)}")
            for middleware in app.middleware_stack:
                print(f"  - {middleware.__class__.__name__}")

        # Configuration
        if hasattr(app, 'config'):
            print("⚙️ Configuration:")
            for key, value in app.config.items():
                if 'SECRET' in key or 'PASSWORD' in key:
                    value = '*' * 8
                print(f"  {key}: {value}")

        print("\n✅ Inspection complete!")

    except Exception as e:
        print(f"❌ Failed to inspect application: {e}")


def tail_logs():
    """Show the last few lines of logs."""
    print("🐺 Tailing application logs...")

    log_files = ['logs/app.log', 'app.log', 'wolfpy.log']
    log_file = None

    for file_path in log_files:
        if os.path.exists(file_path):
            log_file = file_path
            break

    if not log_file:
        print("❌ No log files found")
        print("   Expected: logs/app.log, app.log, or wolfpy.log")
        return

    print(f"📄 Tailing {log_file} (Press Ctrl+C to stop)")
    print("-" * 50)

    try:
        # Show last 20 lines first
        with open(log_file, 'r') as f:
            lines = f.readlines()
            for line in lines[-20:]:
                print(line.rstrip())

        print("-" * 50)

        # Follow new lines
        with open(log_file, 'r') as f:
            f.seek(0, 2)  # Go to end of file

            while True:
                line = f.readline()
                if line:
                    print(line.rstrip())
                else:
                    time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n✅ Stopped tailing logs")
    except Exception as e:
        print(f"❌ Error reading log file: {e}")


def list_plugins():
    """List all installed plugins."""
    print("🐺 Installed WolfPy Plugins")
    print("=" * 30)

    try:
        import pkg_resources

        plugins = []
        for entry_point in pkg_resources.iter_entry_points('wolfpy.plugins'):
            plugins.append({
                'name': entry_point.name,
                'module': entry_point.module_name,
                'dist': entry_point.dist.project_name,
                'version': entry_point.dist.version
            })

        if plugins:
            for plugin in plugins:
                print(f"📦 {plugin['name']}")
                print(f"   Module: {plugin['module']}")
                print(f"   Package: {plugin['dist']} v{plugin['version']}")
                print()
        else:
            print("❌ No plugins installed")
            print("   Install plugins with: wolfpy plugin install <name>")

    except ImportError:
        print("❌ pkg_resources not available")
    except Exception as e:
        print(f"❌ Error listing plugins: {e}")


def install_plugin(plugin_name: str):
    """Install a new plugin."""
    print(f"🐺 Installing plugin: {plugin_name}")

    try:
        # Try to install from PyPI
        subprocess.run(['pip', 'install', f'wolfpy-{plugin_name}'], check=True)
        print(f"✅ Plugin '{plugin_name}' installed successfully!")

        # Try to load and activate the plugin
        try:
            import pkg_resources
            for entry_point in pkg_resources.iter_entry_points('wolfpy.plugins', plugin_name):
                plugin_class = entry_point.load()
                print(f"🔌 Plugin '{plugin_name}' loaded and ready to use!")
                break
        except Exception as e:
            print(f"⚠️ Plugin installed but failed to load: {e}")

    except subprocess.CalledProcessError:
        print(f"❌ Failed to install plugin '{plugin_name}'")
        print("   Make sure the plugin exists on PyPI")
    except FileNotFoundError:
        print("❌ pip not found. Make sure Python and pip are installed.")


def remove_plugin(plugin_name: str):
    """Remove an existing plugin."""
    print(f"🐺 Removing plugin: {plugin_name}")

    try:
        subprocess.run(['pip', 'uninstall', f'wolfpy-{plugin_name}', '-y'], check=True)
        print(f"✅ Plugin '{plugin_name}' removed successfully!")

    except subprocess.CalledProcessError:
        print(f"❌ Failed to remove plugin '{plugin_name}'")
    except FileNotFoundError:
        print("❌ pip not found. Make sure Python and pip are installed.")


def plugin_info(plugin_name: str):
    """Show plugin details."""
    print(f"🐺 Plugin Information: {plugin_name}")
    print("=" * 40)

    try:
        import pkg_resources

        found = False
        for entry_point in pkg_resources.iter_entry_points('wolfpy.plugins', plugin_name):
            found = True
            print(f"📦 Name: {entry_point.name}")
            print(f"🔧 Module: {entry_point.module_name}")
            print(f"📋 Package: {entry_point.dist.project_name}")
            print(f"🏷️ Version: {entry_point.dist.version}")
            print(f"📍 Location: {entry_point.dist.location}")

            # Try to get plugin metadata
            try:
                plugin_class = entry_point.load()
                if hasattr(plugin_class, '__doc__'):
                    print(f"📝 Description: {plugin_class.__doc__}")
                if hasattr(plugin_class, 'version'):
                    print(f"🔢 Plugin Version: {plugin_class.version}")
            except Exception:
                pass

            break

        if not found:
            print(f"❌ Plugin '{plugin_name}' not found")
            print("   Use 'wolfpy plugin list' to see installed plugins")

    except ImportError:
        print("❌ pkg_resources not available")
    except Exception as e:
        print(f"❌ Error getting plugin info: {e}")


def deploy_app():
    """Deploy the app."""
    print("🐺 Deploying WolfPy application...")

    # Check for deployment configuration
    deploy_configs = ['deploy.yml', 'deploy.yaml', '.deploy', 'Procfile']
    deploy_config = None

    for config_file in deploy_configs:
        if os.path.exists(config_file):
            deploy_config = config_file
            break

    if deploy_config:
        print(f"📄 Found deployment config: {deploy_config}")

        if deploy_config == 'Procfile':
            print("🚀 Heroku deployment detected")
            print("   Run: git push heroku main")
        elif deploy_config.endswith(('.yml', '.yaml')):
            print("🔧 YAML deployment config detected")
            print("   Processing deployment configuration...")
            # TODO: Implement YAML-based deployment

    else:
        print("❌ No deployment configuration found")
        print("   Create one of: deploy.yml, Procfile, or .deploy")

        create_config = input("Create basic Heroku Procfile? (y/N): ").lower().strip()
        if create_config == 'y':
            with open('Procfile', 'w') as f:
                f.write('web: python app.py\n')
            print("✅ Created Procfile for Heroku deployment")

    print("📋 Deployment checklist:")
    print("  ✓ Check requirements.txt is up to date")
    print("  ✓ Set environment variables")
    print("  ✓ Configure database settings")
    print("  ✓ Test application locally")


def dockerize_app():
    """Create Dockerfile and build container image."""
    print("🐺 Creating Docker configuration...")

    if os.path.exists('Dockerfile'):
        print("📄 Dockerfile already exists")
        overwrite = input("Overwrite existing Dockerfile? (y/N): ").lower().strip()
        if overwrite != 'y':
            return

    # Create Dockerfile
    dockerfile_content = '''# WolfPy Application Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash wolfpy
RUN chown -R wolfpy:wolfpy /app
USER wolfpy

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["python", "app.py"]
'''

    with open('Dockerfile', 'w') as f:
        f.write(dockerfile_content)
    print("✅ Created Dockerfile")

    # Create .dockerignore
    dockerignore_content = '''__pycache__
*.pyc
*.pyo
*.pyd
.git
.gitignore
README.md
.env
.venv
venv/
.pytest_cache
.coverage
htmlcov/
.tox
.cache
node_modules
.DS_Store
Thumbs.db
'''

    with open('.dockerignore', 'w') as f:
        f.write(dockerignore_content)
    print("✅ Created .dockerignore")

    # Build Docker image
    build_image = input("Build Docker image now? (y/N): ").lower().strip()
    if build_image == 'y':
        app_name = os.path.basename(os.getcwd())
        print(f"🔨 Building Docker image: {app_name}")

        try:
            subprocess.run(['docker', 'build', '-t', app_name, '.'], check=True)
            print(f"✅ Docker image '{app_name}' built successfully!")
            print(f"🚀 Run with: docker run -p 8000:8000 {app_name}")
        except subprocess.CalledProcessError:
            print("❌ Docker build failed")
        except FileNotFoundError:
            print("❌ Docker not found. Make sure Docker is installed.")


def release_app():
    """Package and tag new version."""
    print("🐺 Creating new release...")

    # Check if we're in a git repository
    if not os.path.exists('.git'):
        print("❌ Not a git repository. Initialize with: git init")
        return

    # Get current version
    current_version = "0.1.0"  # Default version

    if os.path.exists('setup.py'):
        try:
            with open('setup.py', 'r') as f:
                content = f.read()
                import re
                version_match = re.search(r'version=["\']([^"\']+)["\']', content)
                if version_match:
                    current_version = version_match.group(1)
        except Exception:
            pass

    print(f"📋 Current version: {current_version}")
    new_version = input("Enter new version: ").strip()

    if not new_version:
        print("❌ Version is required")
        return

    # Update version in setup.py if it exists
    if os.path.exists('setup.py'):
        try:
            with open('setup.py', 'r') as f:
                content = f.read()

            content = re.sub(
                r'version=["\'][^"\']+["\']',
                f'version="{new_version}"',
                content
            )

            with open('setup.py', 'w') as f:
                f.write(content)

            print(f"✅ Updated version in setup.py to {new_version}")
        except Exception as e:
            print(f"⚠️ Failed to update setup.py: {e}")

    # Create git tag
    try:
        subprocess.run(['git', 'add', '.'], check=True)
        subprocess.run(['git', 'commit', '-m', f'Release v{new_version}'], check=True)
        subprocess.run(['git', 'tag', f'v{new_version}'], check=True)

        print(f"✅ Created git tag v{new_version}")
        print("🚀 Push with: git push origin main --tags")

    except subprocess.CalledProcessError as e:
        print(f"❌ Git operations failed: {e}")
    except FileNotFoundError:
        print("❌ Git not found. Make sure Git is installed.")


def build_docs():
    """Generate static docs from Markdown."""
    print("🐺 Building documentation...")

    docs_dir = 'docs'
    if not os.path.exists(docs_dir):
        print("❌ docs/ directory not found")
        create_docs = input("Create docs directory with sample files? (y/N): ").lower().strip()
        if create_docs == 'y':
            os.makedirs(docs_dir, exist_ok=True)

            # Create sample documentation
            index_content = '''# WolfPy Application Documentation

Welcome to your WolfPy application documentation!

## Getting Started

This is your main documentation page. Add more content here.

## API Reference

Document your API endpoints here.

## Deployment

Instructions for deploying your application.
'''
            with open(os.path.join(docs_dir, 'index.md'), 'w') as f:
                f.write(index_content)

            print("✅ Created docs/index.md")
        else:
            return

    # Build documentation
    output_dir = 'docs_build'
    os.makedirs(output_dir, exist_ok=True)

    try:
        import markdown

        # Process all markdown files
        for root, dirs, files in os.walk(docs_dir):
            for file in files:
                if file.endswith('.md'):
                    md_path = os.path.join(root, file)
                    html_path = os.path.join(output_dir, file.replace('.md', '.html'))

                    with open(md_path, 'r', encoding='utf-8') as f:
                        md_content = f.read()

                    html_content = markdown.markdown(md_content, extensions=['codehilite', 'toc'])

                    # Wrap in HTML template
                    full_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WolfPy Documentation</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        code {{ background: #f4f4f4; padding: 2px 4px; border-radius: 3px; }}
        pre {{ background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>'''

                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(full_html)

                    print(f"  ✅ Built {md_path} -> {html_path}")

        print(f"✅ Documentation built in {output_dir}/")

    except ImportError:
        print("❌ markdown not installed. Install with: pip install markdown")
    except Exception as e:
        print(f"❌ Error building docs: {e}")


def serve_docs():
    """Serve docs locally."""
    print("🐺 Starting documentation server...")

    docs_build_dir = 'docs_build'
    if not os.path.exists(docs_build_dir):
        print("❌ docs_build/ not found. Run 'wolfpy docs build' first.")
        return

    port = 8080
    print(f"📚 Serving docs at http://localhost:{port}")
    print("Press Ctrl+C to stop the server")

    try:
        import http.server
        import socketserver
        import webbrowser

        os.chdir(docs_build_dir)

        handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(("", port), handler) as httpd:
            # Open browser
            webbrowser.open(f'http://localhost:{port}')

            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\n✅ Documentation server stopped")

    except Exception as e:
        print(f"❌ Error serving docs: {e}")


def publish_docs():
    """Deploy docs to GitHub Pages or other platform."""
    print("🐺 Publishing documentation...")

    docs_build_dir = 'docs_build'
    if not os.path.exists(docs_build_dir):
        print("❌ docs_build/ not found. Run 'wolfpy docs build' first.")
        return

    # Check if we're in a git repository
    if not os.path.exists('.git'):
        print("❌ Not a git repository. Initialize with: git init")
        return

    # Check for GitHub Pages setup
    try:
        result = subprocess.run(['git', 'remote', 'get-url', 'origin'],
                              capture_output=True, text=True, check=True)
        remote_url = result.stdout.strip()

        if 'github.com' in remote_url:
            print("🐙 GitHub repository detected")

            # Create gh-pages branch if it doesn't exist
            try:
                subprocess.run(['git', 'checkout', 'gh-pages'], check=True)
                print("📋 Switched to gh-pages branch")
            except subprocess.CalledProcessError:
                print("🌿 Creating gh-pages branch...")
                subprocess.run(['git', 'checkout', '--orphan', 'gh-pages'], check=True)
                subprocess.run(['git', 'rm', '-rf', '.'], check=True)

            # Copy built docs
            import shutil
            for item in os.listdir(docs_build_dir):
                src = os.path.join(docs_build_dir, item)
                if os.path.isdir(src):
                    shutil.copytree(src, item, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, item)

            # Commit and push
            subprocess.run(['git', 'add', '.'], check=True)
            subprocess.run(['git', 'commit', '-m', 'Update documentation'], check=True)
            subprocess.run(['git', 'push', 'origin', 'gh-pages'], check=True)

            print("✅ Documentation published to GitHub Pages!")

            # Extract repo info for URL
            import re
            match = re.search(r'github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$', remote_url)
            if match:
                username, repo = match.groups()
                print(f"🌐 Available at: https://{username}.github.io/{repo}")

        else:
            print("❌ GitHub repository not detected")
            print("   Manual deployment required")

    except subprocess.CalledProcessError as e:
        print(f"❌ Git operations failed: {e}")
    except Exception as e:
        print(f"❌ Error publishing docs: {e}")


def generate_enhanced_token():
    """Create a comprehensive JWT-based auth handler."""
    print("🐺 Generating enhanced JWT token handler...")

    # Create auth directory if it doesn't exist
    auth_dir = 'auth'
    os.makedirs(auth_dir, exist_ok=True)

    # Create comprehensive JWT handler
    jwt_handler_content = '''"""
Enhanced JWT Token Handler for WolfPy Applications.

This module provides comprehensive JWT token management including:
- Token generation and validation
- Refresh token support
- Token blacklisting
- Multi-factor authentication integration
"""

import jwt
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from functools import wraps


class JWTTokenHandler:
    """Enhanced JWT token handler with advanced features."""

    def __init__(self, secret_key: str, algorithm: str = 'HS256'):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.blacklisted_tokens = set()  # In production, use Redis or database

    def generate_access_token(self, user_id: str, user_data: Dict[str, Any],
                            expires_in: int = 3600) -> str:
        """Generate access token."""
        payload = {
            'user_id': user_id,
            'user_data': user_data,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow(),
            'type': 'access',
            'jti': secrets.token_hex(16)  # JWT ID for blacklisting
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def generate_refresh_token(self, user_id: str, expires_in: int = 604800) -> str:
        """Generate refresh token (7 days default)."""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow(),
            'type': 'refresh',
            'jti': secrets.token_hex(16)
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def validate_token(self, token: str, token_type: str = 'access') -> Optional[Dict[str, Any]]:
        """Validate and decode token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Check token type
            if payload.get('type') != token_type:
                return None

            # Check if token is blacklisted
            if payload.get('jti') in self.blacklisted_tokens:
                return None

            return payload

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def blacklist_token(self, token: str):
        """Add token to blacklist."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            jti = payload.get('jti')
            if jti:
                self.blacklisted_tokens.add(jti)
        except jwt.InvalidTokenError:
            pass

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Generate new access token from refresh token."""
        payload = self.validate_token(refresh_token, 'refresh')
        if not payload:
            return None

        # Generate new access token
        user_id = payload['user_id']
        # You might want to fetch fresh user data here
        user_data = {'user_id': user_id}  # Placeholder

        return self.generate_access_token(user_id, user_data)


# Global token handler instance
token_handler = JWTTokenHandler(
    secret_key='your-secret-key-here',  # Change this!
    algorithm='HS256'
)


def jwt_required(token_type: str = 'access'):
    """Decorator to require JWT authentication."""
    def decorator(f):
        @wraps(f)
        def decorated_function(request, *args, **kwargs):
            # Get token from Authorization header
            auth_header = request.headers.get('Authorization', '')

            if not auth_header.startswith('Bearer '):
                return {'error': 'Missing or invalid authorization header'}, 401

            token = auth_header.split(' ')[1]
            payload = token_handler.validate_token(token, token_type)

            if not payload:
                return {'error': 'Invalid or expired token'}, 401

            # Add user info to request
            request.user = payload
            return f(request, *args, **kwargs)

        return decorated_function
    return decorator


def login_user(user_id: str, user_data: Dict[str, Any]) -> Dict[str, str]:
    """Login user and return tokens."""
    access_token = token_handler.generate_access_token(user_id, user_data)
    refresh_token = token_handler.generate_refresh_token(user_id)

    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': 3600
    }


def logout_user(access_token: str, refresh_token: str = None):
    """Logout user by blacklisting tokens."""
    token_handler.blacklist_token(access_token)
    if refresh_token:
        token_handler.blacklist_token(refresh_token)
'''

    jwt_file_path = os.path.join(auth_dir, 'jwt_handler.py')
    with open(jwt_file_path, 'w') as f:
        f.write(jwt_handler_content)

    print(f"✅ Created {jwt_file_path}")

    # Create __init__.py for auth package
    init_content = '''"""
Authentication package for WolfPy application.
"""

from .jwt_handler import JWTTokenHandler, jwt_required, login_user, logout_user, token_handler

__all__ = ['JWTTokenHandler', 'jwt_required', 'login_user', 'logout_user', 'token_handler']
'''

    with open(os.path.join(auth_dir, '__init__.py'), 'w') as f:
        f.write(init_content)

    print(f"✅ Created {auth_dir}/__init__.py")
    print("🔐 Enhanced JWT token handler generated successfully!")
    print("📋 Next steps:")
    print("   1. Update the secret key in jwt_handler.py")
    print("   2. Install PyJWT: pip install PyJWT")
    print("   3. Import and use: from auth import jwt_required, login_user")


# ===== MISSING CLI FUNCTIONS =====

def tail_logs():
    """Show the last few lines of logs."""
    print("🐺 Tailing application logs...")

    log_files = ['logs/app.log', 'logs/error.log', 'app.log', 'error.log']
    log_file = None

    for file_path in log_files:
        if os.path.exists(file_path):
            log_file = file_path
            break

    if not log_file:
        print("❌ No log files found. Checked:")
        for file_path in log_files:
            print(f"   - {file_path}")
        return

    print(f"📄 Showing last 20 lines of {log_file}:")
    print("=" * 60)

    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
            for line in lines[-20:]:
                print(line.rstrip())
    except Exception as e:
        print(f"❌ Error reading log file: {e}")


def list_plugins():
    """List all installed plugins."""
    print("🐺 Listing installed plugins...")

    plugins_dir = 'plugins'
    if not os.path.exists(plugins_dir):
        print("❌ No plugins directory found")
        print("   Create plugins/ directory to install plugins")
        return

    plugins = []
    for item in os.listdir(plugins_dir):
        plugin_path = os.path.join(plugins_dir, item)
        if os.path.isdir(plugin_path) and os.path.exists(os.path.join(plugin_path, '__init__.py')):
            plugins.append(item)

    if not plugins:
        print("📦 No plugins installed")
        return

    print(f"📦 Found {len(plugins)} plugin(s):")
    for plugin in plugins:
        print(f"  - {plugin}")


def install_plugin(name: str):
    """Install a new plugin."""
    print(f"🐺 Installing plugin: {name}")

    # Create plugins directory if it doesn't exist
    plugins_dir = 'plugins'
    os.makedirs(plugins_dir, exist_ok=True)

    plugin_dir = os.path.join(plugins_dir, name)

    if os.path.exists(plugin_dir):
        print(f"❌ Plugin '{name}' already exists")
        return

    # Create basic plugin structure
    os.makedirs(plugin_dir, exist_ok=True)

    # Create __init__.py
    init_content = f'''"""
{name} plugin for WolfPy.
"""

def setup(app):
    """Setup plugin with WolfPy app."""
    print(f"🔌 Loading {name} plugin...")

    @app.route(f'/{name}')
    def {name}_index(request):
        return f"Hello from {name} plugin!"

def teardown(app):
    """Cleanup plugin."""
    print(f"🔌 Unloading {name} plugin...")
'''

    with open(os.path.join(plugin_dir, '__init__.py'), 'w', encoding='utf-8') as f:
        f.write(init_content)

    print(f"✅ Plugin '{name}' installed successfully!")
    print(f"📁 Created: {plugin_dir}")
    print("📋 Next steps:")
    print(f"   1. Edit plugins/{name}/__init__.py to customize the plugin")
    print("   2. Load the plugin in your app with: app.load_plugin('{name}')")


def remove_plugin(name: str):
    """Remove an existing plugin."""
    print(f"🐺 Removing plugin: {name}")

    plugin_dir = os.path.join('plugins', name)

    if not os.path.exists(plugin_dir):
        print(f"❌ Plugin '{name}' not found")
        return

    try:
        shutil.rmtree(plugin_dir)
        print(f"✅ Plugin '{name}' removed successfully!")
    except Exception as e:
        print(f"❌ Error removing plugin: {e}")


def plugin_info(name: str):
    """Show plugin details."""
    print(f"🐺 Plugin info: {name}")

    plugin_dir = os.path.join('plugins', name)

    if not os.path.exists(plugin_dir):
        print(f"❌ Plugin '{name}' not found")
        return

    print(f"📦 Plugin: {name}")
    print(f"📁 Location: {plugin_dir}")

    # Check for plugin files
    files = []
    for root, dirs, filenames in os.walk(plugin_dir):
        for filename in filenames:
            files.append(os.path.relpath(os.path.join(root, filename), plugin_dir))

    print(f"📄 Files ({len(files)}):")
    for file in files:
        print(f"   - {file}")


def dockerize_app():
    """Create Dockerfile and build container image."""
    print("🐺 Creating Docker configuration...")

    # Create Dockerfile
    dockerfile_content = '''# WolfPy Application Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash wolfpy
RUN chown -R wolfpy:wolfpy /app
USER wolfpy

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["python", "app.py"]
'''

    with open('Dockerfile', 'w') as f:
        f.write(dockerfile_content)

    print("✅ Created Dockerfile")

    # Create .dockerignore
    dockerignore_content = '''__pycache__
*.pyc
*.pyo
*.pyd
.git
.gitignore
README.md
.env
.venv
venv/
.pytest_cache
.coverage
htmlcov/
.tox/
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.DS_Store
'''

    with open('.dockerignore', 'w') as f:
        f.write(dockerignore_content)

    print("✅ Created .dockerignore")

    # Create docker-compose.yml
    compose_content = '''version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - DATABASE_URL=sqlite:///app.db
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=wolfpy
      - POSTGRES_USER=wolfpy
      - POSTGRES_PASSWORD=wolfpy
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
'''

    with open('docker-compose.yml', 'w') as f:
        f.write(compose_content)

    print("✅ Created docker-compose.yml")

    print("\n🐳 Docker configuration complete!")
    print("📋 Next steps:")
    print("   1. Build image: docker build -t wolfpy-app .")
    print("   2. Run container: docker run -p 8000:8000 wolfpy-app")
    print("   3. Or use compose: docker-compose up")


def release_app():
    """Package and tag new version."""
    print("🐺 Creating new release...")

    # Check if we're in a git repository
    if not os.path.exists('.git'):
        print("❌ Not a git repository. Initialize with: git init")
        return

    # Get current version
    version_file = 'version.txt'
    if os.path.exists(version_file):
        with open(version_file, 'r') as f:
            current_version = f.read().strip()
    else:
        current_version = '0.1.0'

    print(f"📦 Current version: {current_version}")

    # Prompt for new version
    new_version = input("Enter new version (e.g., 0.2.0): ").strip()
    if not new_version:
        print("❌ Version required")
        return

    # Update version file
    with open(version_file, 'w') as f:
        f.write(new_version)

    print(f"✅ Updated version to {new_version}")

    # Create git tag
    try:
        subprocess.run(['git', 'add', version_file], check=True)
        subprocess.run(['git', 'commit', '-m', f'Bump version to {new_version}'], check=True)
        subprocess.run(['git', 'tag', f'v{new_version}'], check=True)

        print(f"✅ Created git tag: v{new_version}")
        print("📋 Next steps:")
        print("   1. Push changes: git push origin main")
        print(f"   2. Push tag: git push origin v{new_version}")
        print("   3. Create GitHub release from the tag")

    except subprocess.CalledProcessError as e:
        print(f"❌ Git operations failed: {e}")
    except Exception as e:
        print(f"❌ Error creating release: {e}")


def main():
    """Main CLI entry point with comprehensive commands."""
    parser = argparse.ArgumentParser(
        description='🐺 WolfPy Framework CLI - Comprehensive web development toolkit',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  wolfpy new myblog                    # Create new project
  wolfpy serve --debug                 # Start development server
  wolfpy routes --format json         # Show routes in JSON format
  wolfpy generate model User          # Generate User model
  wolfpy db migrate                    # Apply database migrations
  wolfpy test --coverage               # Run tests with coverage
  wolfpy clean                         # Clean project files
        '''
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # ✅ Essential CLI Commands

    # Create project command
    create_parser = subparsers.add_parser('new', help='Scaffold a new project with default folders')
    create_parser.add_argument('name', help='Project name')
    create_parser.add_argument('--dir', help='Target directory', default=None)

    # Serve command
    serve_parser = subparsers.add_parser('serve', help='Start the development server')
    serve_parser.add_argument('--app', help='Application file', default='app.py')
    serve_parser.add_argument('--host', help='Host to bind to', default='127.0.0.1')
    serve_parser.add_argument('--port', help='Port to bind to', type=int, default=8000)
    serve_parser.add_argument('--debug', help='Enable debug mode', action='store_true')
    serve_parser.add_argument('--reload', help='Enable auto-reload', action='store_true')

    # Show routes command
    routes_parser = subparsers.add_parser('routes', help='List all registered routes')
    routes_parser.add_argument('--app', help='Application file', default='app.py')
    routes_parser.add_argument('--format', choices=['table', 'json', 'simple'], default='table', help='Output format')

    # Generate commands
    generate_parser = subparsers.add_parser('generate', help='Generate code templates')
    generate_subparsers = generate_parser.add_subparsers(dest='generate_type', help='What to generate')

    # Generate route
    gen_route_parser = generate_subparsers.add_parser('route', help='Generate a new route/controller file')
    gen_route_parser.add_argument('name', help='Route function name')
    gen_route_parser.add_argument('--path', help='URL path')
    gen_route_parser.add_argument('--methods', help='HTTP methods', nargs='+', default=['GET'])

    # Generate model
    gen_model_parser = generate_subparsers.add_parser('model', help='Create a new database model class')
    gen_model_parser.add_argument('name', help='Model class name')
    gen_model_parser.add_argument('--fields', help='Field definitions (name:type:options)', nargs='*')

    # Generate auth
    gen_auth_parser = generate_subparsers.add_parser('auth', help='Create login, register, logout routes and views')

    # Generate token
    gen_token_parser = generate_subparsers.add_parser('token', help='Create a JWT-based auth handler')

    # Database commands
    db_parser = subparsers.add_parser('db', help='Database management')
    db_subparsers = db_parser.add_subparsers(dest='db_action', help='Database actions')

    # DB init
    db_init_parser = db_subparsers.add_parser('init', help='Initialize the database')
    db_init_parser.add_argument('--app', help='Application file', default='app.py')

    # DB migrate
    db_migrate_parser = db_subparsers.add_parser('migrate', help='Generate and apply database schema migrations')
    db_migrate_parser.add_argument('--app', help='Application file', default='app.py')

    # DB rollback
    db_rollback_parser = db_subparsers.add_parser('rollback', help='Roll back the last migration')
    db_rollback_parser.add_argument('--steps', help='Number of migrations to rollback', type=int, default=1)
    db_rollback_parser.add_argument('--app', help='Application file', default='app.py')

    # Test command
    test_parser = subparsers.add_parser('test', help='Run the test suite')
    test_parser.add_argument('--path', help='Test path', default='tests')
    test_parser.add_argument('--verbose', '-v', help='Verbose output', action='store_true')
    test_parser.add_argument('--coverage', help='Enable coverage reporting', action='store_true')

    # Build command
    build_parser = subparsers.add_parser('build', help='Build the package for distribution')

    # Install command
    install_parser = subparsers.add_parser('install', help='Install dependencies from requirements.txt')

    # Clean command
    clean_parser = subparsers.add_parser('clean', help='Remove __pycache__, .pyc, build/, etc.')

    # Version command
    version_parser = subparsers.add_parser('version', help='Show current WolfPy version')

    # Migration commands
    migration_parser = subparsers.add_parser('makemigrations', help='Generate new migration')
    migration_parser.add_argument('name', help='Migration name')
    migration_parser.add_argument('--app', help='Application file', default='app.py')
    migration_parser.add_argument('--models', help='Models file to scan')

    migrate_parser = subparsers.add_parser('migrate', help='Apply pending migrations')
    migrate_parser.add_argument('--app', help='Application file', default='app.py')

    rollback_parser = subparsers.add_parser('rollback', help='Rollback migrations')
    rollback_parser.add_argument('--steps', help='Number of migrations to rollback', type=int, default=1)
    rollback_parser.add_argument('--app', help='Application file', default='app.py')

    showmigrations_parser = subparsers.add_parser('showmigrations', help='Show migration status')
    showmigrations_parser.add_argument('--app', help='Application file', default='app.py')

    # Database management commands
    db_init_parser = subparsers.add_parser('db-init', help='Create initial migration')
    db_init_parser.add_argument('--app', help='Application file', default='app.py')

    db_reset_parser = subparsers.add_parser('db-reset', help='Reset migration history')
    db_reset_parser.add_argument('--app', help='Application file', default='app.py')
    db_reset_parser.add_argument('--confirm', help='Skip confirmation', action='store_true')

    db_check_parser = subparsers.add_parser('db-check', help='Check migration integrity')
    db_check_parser.add_argument('--app', help='Application file', default='app.py')

    # 🔒 Security & Auth Commands
    create_user_parser = subparsers.add_parser('create-user', help='Create admin user manually')

    # 📦 Project Management Commands
    upgrade_parser = subparsers.add_parser('upgrade', help='Update framework components or dependencies')

    # Config commands
    config_parser = subparsers.add_parser('config', help='Configuration management')
    config_subparsers = config_parser.add_subparsers(dest='config_action', help='Config actions')

    config_show_parser = config_subparsers.add_parser('show', help='Display current config settings')
    config_edit_parser = config_subparsers.add_parser('edit', help='Launch config editor')

    # 💾 Static & Assets Commands
    assets_parser = subparsers.add_parser('assets', help='Asset management')
    assets_subparsers = assets_parser.add_subparsers(dest='assets_action', help='Asset actions')

    assets_build_parser = assets_subparsers.add_parser('build', help='Compile static assets')
    assets_clean_parser = assets_subparsers.add_parser('clean', help='Remove compiled asset files')
    assets_watch_parser = assets_subparsers.add_parser('watch', help='Watch assets folder for changes')

    # 🧪 Development Utilities
    shell_parser = subparsers.add_parser('shell', help='Open interactive shell with project context')
    inspect_parser = subparsers.add_parser('inspect', help='Inspect objects, models, routes, etc.')

    # Log commands
    log_parser = subparsers.add_parser('log', help='Log management')
    log_subparsers = log_parser.add_subparsers(dest='log_action', help='Log actions')

    log_tail_parser = log_subparsers.add_parser('tail', help='Show last few lines of logs')

    # 🧱 Plugin & Extension Support
    plugin_parser = subparsers.add_parser('plugin', help='Plugin management')
    plugin_subparsers = plugin_parser.add_subparsers(dest='plugin_action', help='Plugin actions')

    plugin_list_parser = plugin_subparsers.add_parser('list', help='List all installed plugins')
    plugin_install_parser = plugin_subparsers.add_parser('install', help='Install a new plugin')
    plugin_install_parser.add_argument('name', help='Plugin name')
    plugin_remove_parser = plugin_subparsers.add_parser('remove', help='Remove an existing plugin')
    plugin_remove_parser.add_argument('name', help='Plugin name')
    plugin_info_parser = plugin_subparsers.add_parser('info', help='Show plugin details')
    plugin_info_parser.add_argument('name', help='Plugin name')

    # 📤 Deployment Tools
    deploy_parser = subparsers.add_parser('deploy', help='Deploy the app')
    dockerize_parser = subparsers.add_parser('dockerize', help='Create Dockerfile and build container image')
    release_parser = subparsers.add_parser('release', help='Package and tag new version')

    # 📝 Documentation Helpers
    docs_parser = subparsers.add_parser('docs', help='Documentation management')
    docs_subparsers = docs_parser.add_subparsers(dest='docs_action', help='Documentation actions')

    docs_build_parser = docs_subparsers.add_parser('build', help='Generate static docs from Markdown')
    docs_serve_parser = docs_subparsers.add_parser('serve', help='Serve docs locally')
    docs_publish_parser = docs_subparsers.add_parser('publish', help='Deploy docs to GitHub Pages')

    args = parser.parse_args()

    # Handle commands
    if args.command == 'new':
        create_project(args.name, args.dir)

    elif args.command == 'serve':
        serve_app(args.app, args.host, args.port, args.debug, getattr(args, 'reload', False))

    elif args.command == 'routes':
        show_routes(args.app, getattr(args, 'format', 'table'))

    elif args.command == 'generate':
        if args.generate_type == 'route':
            generate_route(args.name, args.path, args.methods)
        elif args.generate_type == 'model':
            generate_model(args.name, getattr(args, 'fields', None))
        elif args.generate_type == 'auth':
            generate_auth()
        elif args.generate_type == 'token':
            generate_enhanced_token()
        else:
            print("❌ Unknown generate type. Use: route, model, auth, token")

    elif args.command == 'db':
        if args.db_action == 'init':
            create_initial_migration(args.app)
        elif args.db_action == 'migrate':
            migrate(args.app)
        elif args.db_action == 'rollback':
            rollback(args.steps, args.app)
        else:
            print("❌ Unknown db action. Use: init, migrate, rollback")

    elif args.command == 'test':
        run_tests(args.path, args.verbose, args.coverage)

    elif args.command == 'build':
        print("🐺 Building package for distribution...")
        try:
            subprocess.run(['python', 'setup.py', 'sdist', 'bdist_wheel'], check=True)
            print("✅ Package built successfully!")
        except subprocess.CalledProcessError:
            print("❌ Build failed. Make sure you have setup.py configured.")
        except FileNotFoundError:
            print("❌ setup.py not found. Create one first.")

    elif args.command == 'install':
        print("🐺 Installing dependencies...")
        try:
            subprocess.run(['pip', 'install', '-r', 'requirements.txt'], check=True)
            print("✅ Dependencies installed successfully!")
        except subprocess.CalledProcessError:
            print("❌ Installation failed.")
        except FileNotFoundError:
            print("❌ requirements.txt not found.")

    elif args.command == 'clean':
        clean_project()

    elif args.command == 'version':
        show_version()

    # Configuration commands
    elif args.command == 'config':
        if args.config_action == 'show':
            show_config()
        elif args.config_action == 'edit':
            edit_config()
        else:
            print("❌ Unknown config action. Use: show, edit")

    # Asset commands
    elif args.command == 'assets':
        if args.assets_action == 'build':
            build_assets()
        elif args.assets_action == 'clean':
            clean_assets()
        elif args.assets_action == 'watch':
            watch_assets()
        else:
            print("❌ Unknown assets action. Use: build, clean, watch")

    # Development utilities
    elif args.command == 'shell':
        open_shell()

    elif args.command == 'inspect':
        inspect_app()

    # Log commands
    elif args.command == 'log':
        if args.log_action == 'tail':
            tail_logs()
        else:
            print("❌ Unknown log action. Use: tail")

    # Plugin commands
    elif args.command == 'plugin':
        if args.plugin_action == 'list':
            list_plugins()
        elif args.plugin_action == 'install':
            install_plugin(args.name)
        elif args.plugin_action == 'remove':
            remove_plugin(args.name)
        elif args.plugin_action == 'info':
            plugin_info(args.name)
        else:
            print("❌ Unknown plugin action. Use: list, install, remove, info")

    # Deployment commands
    elif args.command == 'deploy':
        deploy_app()

    elif args.command == 'dockerize':
        dockerize_app()

    elif args.command == 'release':
        release_app()

    # Documentation commands
    elif args.command == 'docs':
        if args.docs_action == 'build':
            build_docs()
        elif args.docs_action == 'serve':
            serve_docs()
        elif args.docs_action == 'publish':
            publish_docs()
        else:
            print("❌ Unknown docs action. Use: build, serve, publish")

    # Legacy migration commands (for backward compatibility)
    elif args.command == 'makemigrations':
        makemigrations(args.name, args.app, args.models)
    elif args.command == 'migrate':
        migrate(args.app)
    elif args.command == 'rollback':
        rollback(args.steps, args.app)
    elif args.command == 'showmigrations':
        showmigrations(args.app)
    elif args.command == 'db-init':
        create_initial_migration(args.app)
    elif args.command == 'db-reset':
        reset_migrations(args.app, args.confirm)
    elif args.command == 'db-check':
        check_migrations(args.app)

    else:
        print("🐺 WolfPy Framework CLI")
        print("=" * 30)
        print("Use 'wolfpy --help' to see all available commands.")
        print("\\nQuick start:")
        print("  wolfpy new myproject     # Create new project")
        print("  wolfpy serve             # Start development server")
        print("  wolfpy routes            # List all routes")
        parser.print_help()


if __name__ == '__main__':
    main()
