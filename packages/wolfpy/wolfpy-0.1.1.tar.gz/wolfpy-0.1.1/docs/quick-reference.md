# 🐺 WolfPy Quick Reference

## 🚀 Installation & Setup

```bash
# Install WolfPy
pip install wolfpy

# Create new project
wolfpy init my-app
cd my-app

# Install development dependencies
pip install -e .[dev]
```

## 📝 Basic App Structure

```python
from wolfpy import WolfPy
from wolfpy.core.response import Response, JSONResponse

app = WolfPy(debug=True)

@app.route('/')
def home(request):
    return Response('Hello World!')

if __name__ == '__main__':
    app.run()
```

## 🛣️ Routing

```python
# Basic route
@app.route('/hello')
def hello(request):
    return Response('Hello!')

# Route with parameters
@app.route('/user/<int:user_id>')
def user(request, user_id):
    return Response(f'User: {user_id}')

# Multiple methods
@app.route('/api/data', methods=['GET', 'POST', 'PUT'])
def api_data(request):
    return JSONResponse({'method': request.method})

# Query parameters
@app.route('/search')
def search(request):
    query = request.args.get('q', '')
    return Response(f'Searching for: {query}')
```

## 🗄️ Database

```python
from wolfpy.database.models import Model, Column, String, Integer

class User(Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(100))

# Setup
app = WolfPy(database_url='sqlite:///app.db')
app.db.create_all()

# CRUD operations
@app.route('/users', methods=['POST'])
def create_user(request):
    data = request.get_json()
    user = User(name=data['name'], email=data['email'])
    app.db.session.add(user)
    app.db.session.commit()
    return JSONResponse({'id': user.id})

@app.route('/users')
def list_users(request):
    users = app.db.session.query(User).all()
    return JSONResponse([{'id': u.id, 'name': u.name} for u in users])
```

## 🎨 Templates

```python
# Setup
app = WolfPy(template_folder='templates')

@app.route('/profile/<name>')
def profile(request, name):
    return app.render_template('profile.html', 
                             name=name, 
                             age=25)
```

Template (`templates/profile.html`):
```html
<!DOCTYPE html>
<html>
<head><title>{{ name }}'s Profile</title></head>
<body>
    <h1>Hello, {{ name }}!</h1>
    <p>Age: {{ age }}</p>
</body>
</html>
```

## 🔐 Authentication

```python
from wolfpy.auth.decorators import login_required, admin_required

@app.route('/dashboard')
@login_required
def dashboard(request):
    return Response(f'Welcome, {request.user.username}!')

@app.route('/admin')
@admin_required
def admin(request):
    return Response('Admin only!')
```

## 🔌 Middleware

```python
from wolfpy.core.middleware import CORSMiddleware, LoggingMiddleware

# Add CORS
app.add_middleware(CORSMiddleware(
    allow_origins=['*'],
    allow_methods=['GET', 'POST']
))

# Add logging
app.add_middleware(LoggingMiddleware())

# Custom middleware
class TimingMiddleware:
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        start_time = time.time()
        response = self.app(environ, start_response)
        duration = time.time() - start_time
        print(f"Request took {duration:.2f}s")
        return response

app.add_middleware(TimingMiddleware)
```

## 🌐 API Development

```python
# Enable API features
app = WolfPy(enable_api_framework=True)

@app.api_route('/api/users', methods=['GET', 'POST'])
def users_api(request):
    if request.method == 'GET':
        return JSONResponse({'users': []})
    elif request.method == 'POST':
        data = request.get_json()
        return JSONResponse({'created': data}, status_code=201)

# Error handling
@app.error_handler(404)
def not_found(error):
    return JSONResponse({'error': 'Not found'}, status_code=404)
```

## 👑 Admin Interface

```python
from wolfpy.admin.core import AdminSite

# Enable admin
app = WolfPy(enable_admin=True)
admin = AdminSite(app)

# Register models
admin.register(User)

# Access at /admin
```

## ⚡ Real-time (WebSockets)

```python
# Enable WebSocket support
app = WolfPy(enable_realtime=True)

@app.websocket('/ws/chat')
async def chat(websocket):
    await websocket.accept()
    
    async for message in websocket.iter_text():
        await websocket.send_text(f"Echo: {message}")
```

## 🧪 Testing

```python
# test_app.py
import pytest
from app import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_home(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Hello' in response.data

def test_api(client):
    response = client.post('/api/users', 
                          json={'name': 'John'})
    assert response.status_code == 201
```

## 🛠️ CLI Commands

```bash
# Development
wolfpy serve                    # Run dev server
wolfpy serve --reload          # Auto-reload
wolfpy serve --port 3000       # Custom port

# Database
wolfpy db init                 # Initialize DB
wolfpy db migrate              # Run migrations
wolfpy db rollback             # Rollback migration

# Testing
wolfpy test                    # Run tests
wolfpy test --coverage         # With coverage

# Building
wolfpy build                   # Build package
```

## 🐳 Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -e .[production]
EXPOSE 8000
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
```

```bash
# Build and run
docker build -t my-app .
docker run -p 8000:8000 my-app

# Or use docker-compose
docker-compose up
```

## ⚙️ Configuration

```python
import os

class Config:
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY')
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///app.db')

app = WolfPy(
    debug=Config.DEBUG,
    secret_key=Config.SECRET_KEY,
    database_url=Config.DATABASE_URL
)
```

## 🚀 Production Deployment

```bash
# With Gunicorn
pip install gunicorn
gunicorn --workers 4 --bind 0.0.0.0:8000 app:app

# With Docker
docker-compose -f docker-compose.prod.yml up -d

# Deploy to Heroku
git push heroku main
```

## 📊 Monitoring & Health Checks

```python
@app.route('/health')
def health_check():
    return JSONResponse({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/metrics')
def metrics():
    return Response('# Prometheus metrics here', 
                   content_type='text/plain')
```

## 🔧 Common Patterns

### Form Handling
```python
@app.route('/contact', methods=['GET', 'POST'])
def contact(request):
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        # Process form
        return app.redirect('/thank-you')
    return app.render_template('contact.html')
```

### File Upload
```python
@app.route('/upload', methods=['POST'])
def upload_file(request):
    file = request.files.get('file')
    if file:
        filename = secure_filename(file.filename)
        file.save(f'uploads/{filename}')
        return JSONResponse({'filename': filename})
    return JSONResponse({'error': 'No file'}, status_code=400)
```

### Pagination
```python
@app.route('/posts')
def posts(request):
    page = int(request.args.get('page', 1))
    per_page = 10
    offset = (page - 1) * per_page
    
    posts = app.db.session.query(Post)\
                          .offset(offset)\
                          .limit(per_page)\
                          .all()
    
    return app.render_template('posts.html', posts=posts, page=page)
```

### Caching
```python
# Enable caching
app = WolfPy(enable_caching=True, cache_url='redis://localhost:6379')

@app.route('/expensive-operation')
def expensive_op(request):
    cache_key = 'expensive_result'
    result = app.cache.get(cache_key)
    
    if result is None:
        result = perform_expensive_operation()
        app.cache.set(cache_key, result, timeout=300)  # 5 minutes
    
    return JSONResponse(result)
```

## 🆘 Troubleshooting

```python
# Debug mode
app = WolfPy(debug=True)  # Shows detailed errors

# Logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check routes
print(app.router.get_routes())

# Database issues
try:
    app.db.session.execute('SELECT 1')
    print("Database connected")
except Exception as e:
    print(f"Database error: {e}")
```

---

**Need more help? Check the [full documentation](user-guide.md)! 🐺**
