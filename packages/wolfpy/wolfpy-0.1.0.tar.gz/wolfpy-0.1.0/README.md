# WolfPy Web Framework 🐺

![WolfPy Framework](docs/images/wolfpy-logo.png)

A lightweight, modular Python web framework built from scratch with a focus on simplicity, performance, and extensibility.

## ✨ Features

![WolfPy Features](docs/images/wolfpy-features.png)

- **🛣️ Simple Routing**: Intuitive URL routing with parameter support
- **🎨 Template Engine**: Mako template integration with fallback support
- **🗄️ Database ORM**: SQLite-based ORM with model definitions and migrations
- **🔐 Authentication**: Built-in user authentication and session management
- **⚙️ Middleware**: Flexible middleware system for request/response processing
- **📁 Static Files**: Static file serving and asset management
- **🛠️ CLI Tools**: Command-line interface for project management
- **🧪 Testing**: Comprehensive test suite with pytest integration

## 🚀 Quick Start

![WolfPy Quick Start](docs/images/wolfpy-quickstart.png)

### Installation

```bash
pip install wolfpy
```

### Create a New Project

```bash
wolfpy new myproject
cd myproject
python app.py
```

### Basic Application

```python
from wolfpy import WolfPy
from wolfpy.core.response import Response

app = WolfPy(debug=True)

@app.route('/')
def home(request):
    return "Hello, WolfPy!"

@app.route('/user/<name>')
def user_profile(request, name):
    return f"Hello, {name}!"

@app.route('/api/data', methods=['POST'])
def api_data(request):
    if request.is_json():
        data = request.json
        return Response.json({'received': data})
    return Response.bad_request('JSON required')

if __name__ == '__main__':
    app.run()
```

## 🏗️ Core Components

![WolfPy Architecture](docs/images/wolfpy-architecture.png)

### 🛣️ Routing

FoxPy provides a flexible routing system with support for:
- Static routes: `/about`, `/contact`
- Dynamic routes: `/user/<name>`, `/post/<int:id>`
- HTTP methods: `GET`, `POST`, `PUT`, `DELETE`, etc.

```python
@app.route('/user/<int:user_id>', methods=['GET', 'POST'])
def user_handler(request, user_id):
    if request.method == 'GET':
        return f"User ID: {user_id}"
    elif request.method == 'POST':
        return "User updated"
```

### Database ORM

Simple SQLite-based ORM with model definitions:

```python
from wolfpy.core.database import Model, StringField, IntegerField, DateTimeField

class User(Model):
    id = IntegerField(primary_key=True)
    username = StringField(max_length=50, unique=True)
    email = StringField(max_length=100)
    created_at = DateTimeField(auto_now_add=True)

# Create tables
db.create_tables(User)

# Create and save a user
user = User(username='john', email='john@example.com')
user.save()

# Query users
users = db.objects(User).filter(username='john').all()
```

### Templates

Mako template integration with automatic fallback:

```python
@app.route('/')
def home(request):
    return app.template_engine.render('home.html', {
        'title': 'Welcome',
        'users': users
    })
```

### Authentication

Built-in authentication system:

```python
from foxpy.core.auth import Auth, login_required

auth = Auth(secret_key='your-secret-key')

@app.route('/protected')
@login_required(auth)
def protected_route(request):
    return f"Hello, {request.user.username}!"
```

### REST API System (Phase 6)

Enhanced REST API functionality with decorators and helpers:

```python
from wolfpy import get_route, post_route, put_route, delete_route, Response

@get_route('/api/users')
def list_users(request):
    return paginate_data(users, page=1, per_page=10)

@post_route('/api/users')
def create_user(request):
    # request.api_data contains automatically parsed JSON
    validation_error = validate_required_fields(request.api_data, ['name', 'email'])
    if validation_error:
        return validation_error

    return Response.api_success(new_user, "User created successfully")

@delete_route('/api/users/<int:user_id>')
def delete_user(request, user_id):
    # Returns 204 No Content automatically
    return None
```

Features:
- **JSON Response Helpers**: `api_success()`, `api_error()`, `paginated_response()`
- **Route Decorators**: `@get_route()`, `@post_route()`, `@put_route()`, `@delete_route()`
- **Status Code Customization**: Comprehensive HTTP status code support
- **Validation Helpers**: `validate_required_fields()`, automatic JSON parsing
- **APIRouter**: Organized route management with prefixes

### Middleware

Flexible middleware system:

```python
from wolfpy.core.middleware import CORSMiddleware, LoggingMiddleware

app.add_middleware(CORSMiddleware())
app.add_middleware(LoggingMiddleware())
```

## CLI Commands

WolfPy includes a command-line interface for common tasks:

```bash
# Create a new project
wolfpy new myproject

# Serve an application
wolfpy serve --app app.py --host 0.0.0.0 --port 8000 --debug

# Generate a new route
wolfpy route user_profile --path "/user/<name>" --methods GET POST

# Show application routes
wolfpy routes --app app.py

# Show version
wolfpy version
```

## 📚 Comprehensive Examples

### 🌟 Complete Blog Application

A full-featured blog with authentication, CRUD operations, and admin interface:

```python
# examples/blog/app.py
from wolfpy import WolfPy
from wolfpy.core.response import Response
from wolfpy.core.database import Model
from wolfpy.auth.decorators import login_required

app = WolfPy(debug=True, database_url='sqlite:///blog.db')

# Blog Post Model
class Post(Model):
    table_name = 'posts'
    fields = {
        'title': 'TEXT NOT NULL',
        'content': 'TEXT NOT NULL',
        'author': 'TEXT NOT NULL',
        'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
    }

# Routes
@app.route('/')
def home(request):
    posts = Post.all()
    return app.template_engine.render('home.html', {'posts': posts})

@app.route('/post/<int:post_id>')
def view_post(request, post_id):
    post = Post.find(post_id)
    return app.template_engine.render('post.html', {'post': post})

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create_post(request):
    if request.method == 'POST':
        Post.create(
            title=request.form['title'],
            content=request.form['content'],
            author=request.user.username
        )
        return Response.redirect('/')
    return app.template_engine.render('create.html')

if __name__ == '__main__':
    app.database.create_tables([Post])
    app.run()
```

### 🚀 RESTful API Application

A modern REST API with authentication and validation:

```python
# examples/api/app.py
from wolfpy import WolfPy
from wolfpy.core.api_decorators import api_route, json_response
from wolfpy.core.database import Model

app = WolfPy(enable_api_framework=True)

class User(Model):
    table_name = 'users'
    fields = {
        'username': 'TEXT UNIQUE NOT NULL',
        'email': 'TEXT UNIQUE NOT NULL',
        'password_hash': 'TEXT NOT NULL'
    }

@api_route('/api/users', methods=['GET'])
def list_users(request):
    users = User.all()
    return json_response([user.to_dict() for user in users])

@api_route('/api/users', methods=['POST'])
def create_user(request):
    data = request.json
    user = User.create(**data)
    return json_response(user.to_dict(), status=201)

@api_route('/api/users/<int:user_id>', methods=['GET'])
def get_user(request, user_id):
    user = User.find(user_id)
    if not user:
        return json_response({'error': 'User not found'}, status=404)
    return json_response(user.to_dict())

if __name__ == '__main__':
    app.run()
```

### 🎮 Real-time Chat Application

WebSocket-powered real-time chat:

```python
# examples/chat/app.py
from wolfpy import WolfPy
from wolfpy.realtime.websocket import WebSocketManager

app = WolfPy(enable_realtime=True)
ws_manager = WebSocketManager()

@app.route('/')
def chat_room(request):
    return app.template_engine.render('chat.html')

@app.websocket('/ws/chat')
async def chat_handler(websocket):
    await ws_manager.connect(websocket)
    try:
        async for message in websocket.iter_text():
            await ws_manager.broadcast(message)
    except Exception:
        pass
    finally:
        await ws_manager.disconnect(websocket)

if __name__ == '__main__':
    app.run()
```

### 🛠️ Running the Examples

```bash
# Clone the repository
git clone https://github.com/manish12ys/wolfpy.git
cd wolfpy

# Install WolfPy
pip install -e .

# Run blog example
cd examples/blog
python app.py

# Run API example
cd examples/api
python app.py

# Run chat example
cd examples/chat
python app.py

# Run admin demo
cd examples
python admin_demo.py
```

## Development

### Running Tests

```bash
pytest tests/
```

### Project Structure

```
wolfpy/
├── src/wolfpy/         # Main package
│   ├── core/           # Core components
│   ├── static/         # Default static files
│   └── templates/      # Default templates
├── cli/                # Command-line interface
├── tests/              # Test suite
├── examples/           # Example applications
└── docs/               # Documentation
```

## 🚀 Installation & Setup

### 📦 From PyPI (Recommended)

```bash
# Install the latest stable version
pip install wolfpy

# Install with optional dependencies
pip install wolfpy[postgresql,redis,all-databases]

# Install development version
pip install wolfpy[dev]
```

### 🔧 From Source

```bash
# Clone the repository
git clone https://github.com/manish12ys/wolfpy.git
cd wolfpy

# Install in development mode
pip install -e .

# Install with all dependencies
pip install -e .[dev,all-databases,production]
```

### 🐳 Using Docker

```bash
# Pull the official image
docker pull wolfpy/wolfpy:latest

# Run a container
docker run -p 8000:8000 wolfpy/wolfpy:latest

# Or use docker-compose
docker-compose up -d
```

## 🌐 Production Deployment

### 🚀 Quick Deployment

```bash
# Using Gunicorn (recommended)
gunicorn --config gunicorn.conf.py app:app

# Using uWSGI
uwsgi --http :8000 --wsgi-file app.py --callable app

# Using Docker
docker build -t my-wolfpy-app .
docker run -p 8000:8000 my-wolfpy-app
```

### ☁️ Cloud Deployment

#### Heroku
```bash
# Create Heroku app
heroku create my-wolfpy-app

# Deploy
git push heroku main

# Scale
heroku ps:scale web=1
```

#### AWS/DigitalOcean
```bash
# Use the provided deployment scripts
python scripts/deploy.py aws
python scripts/deploy.py digitalocean
```

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### 🛠️ Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/yourusername/wolfpy.git
cd wolfpy

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e .[dev,all-databases]

# Run tests to ensure everything works
pytest tests/
```

### 📝 Contribution Guidelines

1. **Fork the repository** and create your feature branch
2. **Write tests** for any new functionality
3. **Follow code style** - we use Black and flake8
4. **Update documentation** if needed
5. **Submit a pull request** with a clear description

### 🧪 Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=wolfpy --cov-report=html

# Run specific test file
pytest tests/test_routing.py -v

# Run linting
flake8 src/wolfpy tests
black --check src/wolfpy tests
```

### 📋 Code Style

We follow PEP 8 with some modifications:

- Line length: 88 characters (Black default)
- Use type hints where possible
- Write docstrings for public functions
- Keep functions focused and small

## License

MIT License - see LICENSE file for details.

## Roadmap

- [x] Core routing and WSGI interface
- [x] Template engine integration
- [x] Database ORM
- [x] Authentication system
- [x] Middleware support
- [x] CLI tools
- [x] REST API System (Phase 6)
- [ ] Async/ASGI support
- [ ] WebSocket support
- [ ] Plugin system
- [ ] Admin interface
- [ ] Production deployment tools

## 📸 Visual Documentation

Our documentation includes comprehensive visual guides and diagrams:

- **🎨 Framework Overview**: Visual representation of WolfPy's architecture and components
- **🚀 Quick Start Guide**: Step-by-step visual tutorials for getting started
- **⚙️ Feature Showcase**: Illustrated examples of core functionality
- **🏗️ Architecture Diagrams**: Clear visual explanations of the framework structure

All images are organized in the `docs/images/` folder for easy reference and maintenance.

## 🆘 Support

- **📖 Documentation**: [Full Documentation](docs/index.md)
- **📧 Email**: [Contact Support](mailto:manishchowdary2006@gmail.com)

