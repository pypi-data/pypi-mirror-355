# WolfPy Framework Documentation

![WolfPy Framework](images/wolfpy-logo.png)

Welcome to the comprehensive documentation for the WolfPy web framework! 🐺

WolfPy is a lightweight, modular Python web framework built from scratch with a focus on simplicity, performance, and extensibility.

## 🚀 Quick Start

Get started with WolfPy in minutes:

```bash
# Install WolfPy
pip install wolfpy

# Create a new project
wolfpy new myproject
cd myproject

# Run your application
python app.py
```

## 📋 Table of Contents

### 🚀 Getting Started

- **[User Guide](user-guide.md)** - Complete guide to using WolfPy
- **[Quick Reference](quick-reference.md)** - Cheat sheet for common tasks
- **[Visual Guide](visual-guide.md)** - Visual documentation and diagrams
- [Getting Started](getting-started.md) - Installation and basic setup

### 🔧 Development

- [API Framework](api.md) - Building REST APIs
- [Plugins](plugins.md) - Plugin system and extensions
- [Real-time Support](phase11-realtime-support.md) - WebSocket and async features

### 🚀 Deployment

- **[Deployment Guide](deployment.md)** - Production deployment
- **[Production Checklist](production-checklist.md)** - Pre-launch checklist

## ✨ Key Features

![WolfPy Features Overview](images/wolfpy-features.png)

### 🛣️ Simple Routing
```python
from wolfpy import WolfPy

app = WolfPy()

@app.route('/')
def home(request):
    return "Hello, WolfPy!"

@app.route('/user/<name>')
def user_profile(request, name):
    return f"Hello, {name}!"
```

### 🎨 Template Engine
```python
@app.route('/dashboard')
def dashboard(request):
    return app.template_engine.render('dashboard.html', {
        'user': request.user,
        'data': get_dashboard_data()
    })
```

### 🗄️ Database ORM
```python
from wolfpy.core.database import Model

class User(Model):
    table_name = 'users'
    fields = {
        'name': 'TEXT NOT NULL',
        'email': 'TEXT UNIQUE NOT NULL',
        'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
    }

# Create a user
user = User.create(name='John Doe', email='john@example.com')

# Query users
users = User.all()
user = User.find_by('email', 'john@example.com')
```

### 🔐 Authentication
```python
@app.route('/login', methods=['POST'])
def login(request):
    if app.auth.authenticate(request.form['email'], request.form['password']):
        return redirect('/dashboard')
    return render_template('login.html', error='Invalid credentials')

@app.route('/protected')
@app.auth.login_required
def protected_route(request):
    return f"Hello, {request.user.name}!"
```

### 🌐 API Framework
```python
from wolfpy.core.api_decorators import api_route, json_response

@api_route('/api/users', methods=['GET'])
def get_users(request):
    users = User.all()
    return json_response([user.to_dict() for user in users])

@api_route('/api/users', methods=['POST'])
def create_user(request):
    user = User.create(**request.json)
    return json_response(user.to_dict(), status=201)
```

## 🏗️ Architecture

![WolfPy Architecture](images/wolfpy-architecture.png)

WolfPy follows a modular architecture with clear separation of concerns:

- **Core Framework** - WSGI application, routing, request/response handling
- **Template Engine** - Mako and Jinja2 support with caching
- **Database Layer** - SQLite-based ORM with migration support
- **Authentication** - Session-based auth with bcrypt password hashing
- **Middleware System** - Pluggable request/response processing
- **API Framework** - RESTful API development tools
- **CLI Tools** - Project scaffolding and development utilities

## 🔧 Configuration

Configure your WolfPy application:

```python
# config/settings.py
import os

config = {
    'DEBUG': os.getenv('DEBUG', 'True').lower() == 'true',
    'SECRET_KEY': os.getenv('SECRET_KEY', 'your-secret-key'),
    'DATABASE_URL': os.getenv('DATABASE_URL', 'sqlite:///app.db'),
    'TEMPLATE_FOLDER': 'templates',
    'STATIC_FOLDER': 'static',
}

def get_config():
    return config
```

## 🧪 Testing

WolfPy includes comprehensive testing utilities:

```python
import pytest
from wolfpy.testing import TestClient

def test_home_route():
    client = TestClient(app)
    response = client.get('/')
    assert response.status_code == 200
    assert 'Hello, WolfPy!' in response.text
```

## 📦 Plugin System

Extend WolfPy with plugins:

```python
# plugins/myplugin/__init__.py
def setup(app):
    """Setup plugin with WolfPy app."""
    @app.route('/myplugin')
    def plugin_route(request):
        return "Hello from my plugin!"

def teardown(app):
    """Cleanup plugin."""
    pass
```

Load plugins in your application:

```python
app = WolfPy()
app.plugin_manager.load_plugin('myplugin')
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](contributing.md) for details.

## 📄 License

WolfPy is released under the MIT License. See [LICENSE](../LICENSE) for details.

## 🆘 Support

- 📖 [Documentation](https://wolfpy.readthedocs.io)
- 🐛 [Issue Tracker](https://github.com/manish/wolfpy/issues)
- 💬 [Discussions](https://github.com/manish/wolfpy/discussions)
- 📧 [Email Support](mailto:manish@example.com)

---

Ready to build amazing web applications with WolfPy? Let's get started! 🚀
