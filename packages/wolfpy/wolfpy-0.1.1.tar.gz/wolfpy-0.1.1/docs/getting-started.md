# Getting Started with WolfPy

![WolfPy Getting Started](images/wolfpy-quickstart.png)

Welcome to WolfPy! This guide will help you get up and running with the WolfPy web framework in just a few minutes.

## 📋 Prerequisites

Before you begin, make sure you have:

- Python 3.9 or higher
- pip (Python package installer)
- A text editor or IDE
- Basic knowledge of Python and web development

## 🚀 Installation

### Install from PyPI

```bash
pip install wolfpy
```

### Install from Source

```bash
git clone https://github.com/manish/wolfpy.git
cd wolfpy
pip install -e .
```

### Verify Installation

```bash
wolfpy --version
```

You should see the WolfPy version information.

## 🏗️ Create Your First Project

![WolfPy Project Structure](images/wolfpy-architecture.png)

### Using the CLI

The easiest way to start is using the WolfPy CLI:

```bash
# Create a new project
wolfpy new myproject

# Navigate to the project directory
cd myproject

# Run the development server
python app.py
```

Your application will be available at `http://localhost:8000`.

### Manual Setup

If you prefer to set up manually:

```python
# app.py
from wolfpy import WolfPy
from wolfpy.core.response import Response

# Create WolfPy application
app = WolfPy(debug=True)

@app.route('/')
def home(request):
    return "Hello, WolfPy! 🐺"

@app.route('/about')
def about(request):
    return Response("""
    <h1>About WolfPy</h1>
    <p>A lightweight, modular Python web framework.</p>
    """)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
```

## 🛣️ Basic Routing

WolfPy uses decorators for route definition:

```python
# Simple routes
@app.route('/')
def home(request):
    return "Welcome to WolfPy!"

@app.route('/hello')
def hello(request):
    return "Hello, World!"

# Routes with parameters
@app.route('/user/<name>')
def user_profile(request, name):
    return f"Hello, {name}!"

@app.route('/post/<int:post_id>')
def show_post(request, post_id):
    return f"Post ID: {post_id}"

# Multiple HTTP methods
@app.route('/contact', methods=['GET', 'POST'])
def contact(request):
    if request.method == 'POST':
        return "Thank you for your message!"
    return "Contact form"
```

## 📝 Request Handling

Access request data easily:

```python
@app.route('/form', methods=['POST'])
def handle_form(request):
    # Form data
    name = request.form.get('name')
    email = request.form.get('email')
    
    # Query parameters
    page = request.args.get('page', 1)
    
    # JSON data
    if request.is_json():
        data = request.json
        return Response.json({'received': data})
    
    # Headers
    user_agent = request.headers.get('User-Agent')
    
    return f"Hello {name}!"

@app.route('/upload', methods=['POST'])
def upload_file(request):
    # File uploads
    if 'file' in request.files:
        file = request.files['file']
        file.save(f'uploads/{file.filename}')
        return "File uploaded successfully!"
    return "No file uploaded"
```

## 📄 Response Types

WolfPy provides various response types:

```python
from wolfpy.core.response import Response

@app.route('/text')
def text_response(request):
    return "Plain text response"

@app.route('/html')
def html_response(request):
    return Response("""
    <html>
        <body>
            <h1>HTML Response</h1>
        </body>
    </html>
    """, content_type='text/html')

@app.route('/json')
def json_response(request):
    return Response.json({
        'message': 'Hello, JSON!',
        'status': 'success'
    })

@app.route('/redirect')
def redirect_response(request):
    return Response.redirect('/home')

@app.route('/error')
def error_response(request):
    return Response.error('Something went wrong!', status=500)
```

## 🎨 Templates

WolfPy supports both Mako and Jinja2 templates:

### Setup Templates

```python
app = WolfPy(
    template_folder='templates',
    debug=True
)

@app.route('/profile/<name>')
def profile(request, name):
    return app.template_engine.render('profile.html', {
        'name': name,
        'title': f'{name}\'s Profile'
    })
```

### Template File (templates/profile.html)

```html
<!DOCTYPE html>
<html>
<head>
    <title>${title}</title>
</head>
<body>
    <h1>Welcome, ${name}!</h1>
    <p>This is your profile page.</p>
</body>
</html>
```

## 🗄️ Database Integration

WolfPy includes a simple ORM:

```python
from wolfpy.core.database import Model

# Define a model
class User(Model):
    table_name = 'users'
    fields = {
        'name': 'TEXT NOT NULL',
        'email': 'TEXT UNIQUE NOT NULL',
        'age': 'INTEGER',
        'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
    }

# Initialize database
app.database.create_tables([User])

@app.route('/users', methods=['POST'])
def create_user(request):
    user = User.create(
        name=request.form['name'],
        email=request.form['email'],
        age=int(request.form['age'])
    )
    return Response.json(user.to_dict())

@app.route('/users')
def list_users(request):
    users = User.all()
    return Response.json([user.to_dict() for user in users])

@app.route('/users/<int:user_id>')
def get_user(request, user_id):
    user = User.find(user_id)
    if user:
        return Response.json(user.to_dict())
    return Response.error('User not found', status=404)
```

## 🔐 Authentication

Add user authentication:

```python
@app.route('/register', methods=['POST'])
def register(request):
    if app.auth.register(
        request.form['email'],
        request.form['password'],
        name=request.form['name']
    ):
        return Response.redirect('/login')
    return Response.error('Registration failed')

@app.route('/login', methods=['POST'])
def login(request):
    if app.auth.authenticate(
        request.form['email'],
        request.form['password']
    ):
        return Response.redirect('/dashboard')
    return Response.error('Invalid credentials')

@app.route('/dashboard')
@app.auth.login_required
def dashboard(request):
    return f"Welcome to your dashboard, {request.user.name}!"

@app.route('/logout')
def logout(request):
    app.auth.logout(request)
    return Response.redirect('/')
```

## 🌐 Static Files

Serve static files (CSS, JS, images):

```python
app = WolfPy(
    static_folder='static',
    debug=True
)
```

Directory structure:
```
myproject/
├── app.py
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── app.js
│   └── images/
│       └── logo.png
└── templates/
    └── index.html
```

Access static files at `/static/css/style.css`, `/static/js/app.js`, etc.

## 🔧 Configuration

Create a configuration file:

```python
# config/settings.py
import os

config = {
    'DEBUG': os.getenv('DEBUG', 'True').lower() == 'true',
    'SECRET_KEY': os.getenv('SECRET_KEY', 'your-secret-key-here'),
    'DATABASE_URL': os.getenv('DATABASE_URL', 'sqlite:///app.db'),
    'UPLOAD_FOLDER': 'uploads',
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB
}

def get_config():
    return config
```

Use configuration in your app:

```python
from config.settings import get_config

config = get_config()
app = WolfPy(
    debug=config['DEBUG'],
    secret_key=config['SECRET_KEY']
)
```

## 🧪 Testing

Write tests for your application:

```python
# test_app.py
import pytest
from wolfpy.testing import TestClient
from app import app

def test_home_route():
    client = TestClient(app)
    response = client.get('/')
    assert response.status_code == 200
    assert 'Hello, WolfPy!' in response.text

def test_user_profile():
    client = TestClient(app)
    response = client.get('/user/john')
    assert response.status_code == 200
    assert 'Hello, john!' in response.text

def test_json_api():
    client = TestClient(app)
    response = client.get('/json')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'success'
```

Run tests:

```bash
pytest test_app.py
```

## 🚀 Development Server

Run your application in development mode:

```bash
# Using the built-in server
python app.py

# Using the CLI
wolfpy serve --app app.py --debug --reload

# Custom host and port
wolfpy serve --app app.py --host 0.0.0.0 --port 5000
```

## 📦 Project Structure

A typical WolfPy project structure:

```
myproject/
├── app.py                 # Main application file
├── config/
│   ├── __init__.py
│   └── settings.py        # Configuration
├── routes/
│   ├── __init__.py
│   ├── main.py           # Main routes
│   ├── api.py            # API routes
│   └── auth.py           # Authentication routes
├── models/
│   ├── __init__.py
│   └── user.py           # Database models
├── templates/
│   ├── base.html         # Base template
│   ├── index.html        # Home page
│   └── profile.html      # Profile page
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── tests/
│   ├── __init__.py
│   └── test_app.py       # Tests
├── requirements.txt       # Dependencies
└── README.md             # Project documentation
```

## 🎯 Next Steps

Now that you have the basics, explore more advanced features:

- [Routing](routing.md) - Advanced routing patterns
- [Templates](templates.md) - Template inheritance and filters
- [Database](database.md) - Migrations and relationships
- [API Framework](api.md) - Building REST APIs
- [Middleware](middleware.md) - Custom middleware
- [Plugins](plugins.md) - Extending with plugins
- [Deployment](deployment.md) - Production deployment

## 🆘 Getting Help

- 📖 [Full Documentation](index.md)
- 🐛 [Report Issues](https://github.com/manish/wolfpy/issues)
- 💬 [Community Discussions](https://github.com/manish/wolfpy/discussions)

Happy coding with WolfPy! 🐺✨
