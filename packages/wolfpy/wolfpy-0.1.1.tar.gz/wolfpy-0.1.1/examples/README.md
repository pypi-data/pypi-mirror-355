# WolfPy Examples 🐺

This directory contains comprehensive examples demonstrating various features of the WolfPy web framework.

## 📚 Available Examples

### 🌟 Blog Application (`blog/`)
A complete blog application showcasing:
- User authentication and registration
- CRUD operations for blog posts
- Template rendering with Mako
- Database models and relationships
- Admin interface for content management
- Static file serving

**Features:**
- User registration and login
- Create, edit, and delete blog posts
- Admin dashboard
- Comment system (basic)
- Responsive design

**Run the blog:**
```bash
cd examples/blog
python app.py
```

**Default admin credentials:**
- Username: `admin`
- Password: `admin123`

### 🚀 REST API (`api/`)
A modern REST API demonstrating:
- RESTful endpoints with proper HTTP methods
- JSON request/response handling
- API authentication with Bearer tokens
- Request validation and error handling
- Pagination and filtering
- API documentation

**Features:**
- User registration and authentication
- Todo task management (CRUD)
- API token-based authentication
- Request validation
- Statistics endpoint
- Health check endpoint

**Run the API:**
```bash
cd examples/api
python app.py
```

**API Documentation:** http://localhost:8000/api/docs

### 🎮 Real-time Chat (`realtime_chat.py`)
WebSocket-powered real-time chat application:
- Real-time messaging
- Multiple chat rooms
- User presence tracking
- Message history
- Connection management

**Run the chat:**
```bash
cd examples
python realtime_chat.py
```

### 🛠️ Admin Demo (`admin_demo.py`)
Demonstrates the built-in admin interface:
- Model registration
- CRUD operations through web interface
- User management
- Data visualization

**Run the admin demo:**
```bash
cd examples
python admin_demo.py
```

### 🔧 Error Handling Demo (`error_handling_demo.py`)
Shows comprehensive error handling:
- Custom error pages
- Exception middleware
- Logging configuration
- Debug vs production modes

**Run the error demo:**
```bash
cd examples
python error_handling_demo.py
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- WolfPy framework installed

### Installation
```bash
# Clone the repository
git clone https://github.com/manish12ys/wolfpy.git
cd wolfpy

# Install WolfPy in development mode
pip install -e .

# Or install from PyPI
pip install wolfpy
```

### Running Examples
Each example is self-contained and can be run independently:

```bash
# Navigate to the example directory
cd examples/blog  # or api, etc.

# Run the application
python app.py

# Visit http://localhost:8000 in your browser
```

## 📖 Learning Path

We recommend exploring the examples in this order:

1. **Blog Application** - Learn the basics of WolfPy
   - Routing and templates
   - Database models
   - Authentication
   - Admin interface

2. **REST API** - Understand API development
   - JSON handling
   - API authentication
   - Request validation
   - Error handling

3. **Real-time Chat** - Explore advanced features
   - WebSocket support
   - Async programming
   - Real-time communication

4. **Admin Demo** - See the admin interface
   - Model registration
   - CRUD operations
   - Data management

5. **Error Handling** - Learn about robustness
   - Exception handling
   - Custom error pages
   - Logging

## 🔧 Customization

Each example can be customized and extended:

### Database Configuration
```python
# SQLite (default)
app = WolfPy(database_url='sqlite:///app.db')

# PostgreSQL
app = WolfPy(database_url='postgresql://user:pass@localhost/db')

# MySQL
app = WolfPy(database_url='mysql://user:pass@localhost/db')
```

### Template Engines
```python
# Mako (default)
app = WolfPy(template_engine='mako')

# Jinja2
app = WolfPy(template_engine='jinja2')
```

### Static Files
```python
app = WolfPy(
    static_folder='static',
    static_url_path='/static'
)
```

## 🧪 Testing Examples

Each example includes basic testing:

```bash
# Run tests for a specific example
cd examples/blog
python -m pytest tests/

# Run all example tests
python -m pytest examples/
```

## 📦 Production Deployment

### Using Gunicorn
```bash
# Install production dependencies
pip install gunicorn

# Run with Gunicorn
cd examples/blog
gunicorn app:app
```

### Using Docker
```bash
# Build Docker image
docker build -t wolfpy-blog examples/blog/

# Run container
docker run -p 8000:8000 wolfpy-blog
```

### Environment Variables
```bash
# Set production environment
export WOLFPY_ENV=production
export SECRET_KEY=your-secret-key
export DATABASE_URL=postgresql://...

# Run application
python app.py
```

## 🤝 Contributing Examples

We welcome contributions of new examples! Please:

1. Create a new directory under `examples/`
2. Include a complete, working application
3. Add documentation and comments
4. Include a README.md explaining the example
5. Add tests if possible
6. Update this main README.md

### Example Structure
```
examples/your-example/
├── app.py              # Main application
├── README.md           # Example documentation
├── requirements.txt    # Dependencies (if any)
├── templates/          # Template files
├── static/            # Static files
└── tests/             # Tests (optional)
```

## 🆘 Getting Help

If you have questions about the examples:

1. Check the [main documentation](../docs/index.md)
2. Look at the code comments in each example
3. Open an issue on [GitHub](https://github.com/manish12ys/wolfpy/issues)
4. Join our [discussions](https://github.com/manish12ys/wolfpy/discussions)

## 📄 License

All examples are released under the MIT License, same as the WolfPy framework.

---

**Happy coding with WolfPy! 🐺✨**
