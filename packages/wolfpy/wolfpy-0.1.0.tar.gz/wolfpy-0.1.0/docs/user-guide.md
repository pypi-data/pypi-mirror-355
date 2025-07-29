# 🐺 WolfPy Framework - User Guide

![WolfPy Framework](images/wolfpy-logo.png)

WolfPy is a modern, modular Python web framework with built-in admin, real-time support, and production-ready deployment features.

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI (when published)
pip install wolfpy

# Or install from source
git clone https://github.com/manish12ys/wolfpy.git
cd wolfpy
pip install -e .
```

### Your First App

Create a simple web application:

```python
# app.py
from wolfpy import WolfPy
from wolfpy.core.response import Response, JSONResponse

# Create app instance
app = WolfPy(debug=True)

# Define routes
@app.route('/')
def home(request):
    return Response('<h1>Hello, WolfPy! 🐺</h1>')

@app.route('/api/hello')
def api_hello(request):
    return JSONResponse({'message': 'Hello from WolfPy API!'})

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
```

Run your app:
```bash
python app.py
```

Visit `http://localhost:8000` to see your app!

## 📖 Core Features

![WolfPy Core Features](images/wolfpy-features.png)

### 1. Routing

```python
from wolfpy import WolfPy

app = WolfPy()

# Basic routes
@app.route('/')
def home(request):
    return Response('Home page')

# Route with parameters
@app.route('/user/<int:user_id>')
def user_profile(request, user_id):
    return Response(f'User ID: {user_id}')

# Multiple HTTP methods
@app.route('/api/data', methods=['GET', 'POST'])
def handle_data(request):
    if request.method == 'GET':
        return JSONResponse({'data': 'Here is your data'})
    elif request.method == 'POST':
        return JSONResponse({'message': 'Data received'})
```

### 2. Templates

```python
# Enable template rendering
app = WolfPy(template_folder='templates')

@app.route('/profile/<name>')
def profile(request, name):
    return app.render_template('profile.html', name=name, age=25)
```

Create `templates/profile.html`:
```html
<!DOCTYPE html>
<html>
<head>
    <title>{{ name }}'s Profile</title>
</head>
<body>
    <h1>Welcome, {{ name }}!</h1>
    <p>Age: {{ age }}</p>
</body>
</html>
```

### 3. Database & Models

```python
from wolfpy.database.models import Model, Column, String, Integer, Boolean

# Define models
class User(Model):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)

# Create app with database
app = WolfPy(database_url='sqlite:///app.db')

# Create tables
app.db.create_all()

# Use in routes
@app.route('/users')
def list_users(request):
    users = app.db.session.query(User).all()
    return JSONResponse([{
        'id': user.id,
        'username': user.username,
        'email': user.email
    } for user in users])
```

### 4. Authentication

```python
from wolfpy.auth.decorators import login_required, admin_required

@app.route('/dashboard')
@login_required
def dashboard(request):
    return Response(f'Welcome to dashboard, {request.user.username}!')

@app.route('/admin')
@admin_required
def admin_panel(request):
    return Response('Admin panel - restricted access')
```

### 5. API Development

```python
# Enable API framework
app = WolfPy(enable_api_framework=True)

@app.api_route('/api/users', methods=['GET', 'POST'])
def users_api(request):
    if request.method == 'GET':
        users = app.db.session.query(User).all()
        return JSONResponse([user.to_dict() for user in users])
    
    elif request.method == 'POST':
        data = request.get_json()
        user = User(username=data['username'], email=data['email'])
        app.db.session.add(user)
        app.db.session.commit()
        return JSONResponse(user.to_dict(), status_code=201)
```

### 6. Admin Interface

```python
from wolfpy.admin.core import AdminSite

# Enable admin
app = WolfPy(enable_admin=True)
admin = AdminSite(app, url_prefix='/admin')

# Register models
admin.register(User)

# Access admin at http://localhost:8000/admin
```

### 7. Real-time Features (WebSockets)

```python
# Enable real-time support
app = WolfPy(enable_realtime=True)

@app.websocket('/ws/chat')
async def chat_handler(websocket):
    await websocket.accept()
    
    async for message in websocket.iter_text():
        # Echo message back
        await websocket.send_text(f"Echo: {message}")
```

### 8. Middleware

```python
from wolfpy.core.middleware import CORSMiddleware, LoggingMiddleware

# Add middleware
app.add_middleware(CORSMiddleware(
    allow_origins=['*'],
    allow_methods=['GET', 'POST', 'PUT', 'DELETE']
))

app.add_middleware(LoggingMiddleware())

# Custom middleware
class CustomMiddleware:
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        # Process request
        print(f"Request: {environ['REQUEST_METHOD']} {environ['PATH_INFO']}")
        return self.app(environ, start_response)

app.add_middleware(CustomMiddleware)
```

## 🛠️ CLI Tools

WolfPy includes powerful CLI tools:

```bash
# Create new project
wolfpy init my-project

# Run development server
wolfpy serve --host 0.0.0.0 --port 8000 --reload

# Database migrations
wolfpy db init
wolfpy db migrate
wolfpy db rollback

# Run tests
wolfpy test

# Build for production
wolfpy build
```

## 🔧 Configuration

### Environment-based Configuration

```python
import os

class Config:
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

app = WolfPy(
    debug=Config.DEBUG,
    secret_key=Config.SECRET_KEY,
    database_url=Config.DATABASE_URL,
    cache_url=Config.REDIS_URL
)
```

### Production Configuration

```python
# production_app.py
app = WolfPy(
    debug=False,
    enable_performance_monitoring=True,
    enable_caching=True,
    enable_api_framework=True,
    database_url=os.getenv('DATABASE_URL'),
    cache_url=os.getenv('REDIS_URL')
)

# Add security middleware
from wolfpy.core.middleware import SecurityMiddleware
app.add_middleware(SecurityMiddleware())
```

## 🚀 Deployment

### Development

```bash
# Run with auto-reload
python app.py

# Or use CLI
wolfpy serve --reload
```

### Production with Docker

```bash
# Build Docker image
docker build -t my-wolfpy-app .

# Run container
docker run -p 8000:8000 my-wolfpy-app

# Or use docker-compose
docker-compose up -d
```

### Production with Gunicorn

```bash
# Install production dependencies
pip install wolfpy[production]

# Run with Gunicorn
gunicorn --config gunicorn.conf.py app:app
```

### Deploy to Cloud

```bash
# Heroku
git push heroku main

# Or use deployment script
python scripts/deploy.py heroku
```

## 📚 Examples

### Complete Blog Application

```python
from wolfpy import WolfPy
from wolfpy.database.models import Model, Column, String, Text, DateTime
from wolfpy.auth.decorators import login_required
from datetime import datetime

# Models
class Post(Model):
    __tablename__ = 'posts'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# App setup
app = WolfPy(
    debug=True,
    database_url='sqlite:///blog.db',
    template_folder='templates',
    static_folder='static'
)

app.db.create_all()

# Routes
@app.route('/')
def home(request):
    posts = app.db.session.query(Post).order_by(Post.created_at.desc()).all()
    return app.render_template('home.html', posts=posts)

@app.route('/post/<int:post_id>')
def view_post(request, post_id):
    post = app.db.session.query(Post).get_or_404(post_id)
    return app.render_template('post.html', post=post)

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create_post(request):
    if request.method == 'POST':
        data = request.form
        post = Post(
            title=data['title'],
            content=data['content'],
            author=request.user.username
        )
        app.db.session.add(post)
        app.db.session.commit()
        return app.redirect('/')
    
    return app.render_template('create.html')

if __name__ == '__main__':
    app.run()
```

## 🔍 Testing

```python
# test_app.py
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Hello, WolfPy!' in response.data

def test_api_endpoint(client):
    response = client.get('/api/hello')
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == 'Hello from WolfPy API!'
```

Run tests:
```bash
pytest tests/
```

## 📖 More Resources

- **[API Documentation](api.md)** - Complete API reference
- **[Deployment Guide](deployment.md)** - Production deployment
- **[Examples](../examples/)** - Sample applications
- **[GitHub Repository](https://github.com/manish12ys/wolfpy)** - Source code

## 🆘 Getting Help

- **Issues**: [GitHub Issues](https://github.com/manish12ys/wolfpy/issues)
- **Discussions**: [GitHub Discussions](https://github.com/manish12ys/wolfpy/discussions)
- **Documentation**: [Full Documentation](https://wolfpy.readthedocs.io)

---

**Happy coding with WolfPy! 🐺✨**
