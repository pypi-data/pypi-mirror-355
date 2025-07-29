# Plugin System

WolfPy features a powerful plugin system that allows you to extend the framework with custom functionality. The plugin system uses Python's `entry_points` mechanism for automatic discovery and provides lifecycle management for plugins.

## 🔌 Plugin Architecture

The WolfPy plugin system is built around several key concepts:

- **Plugin Discovery** - Automatic discovery using `entry_points` and local plugin directories
- **Lifecycle Management** - Setup and teardown hooks for proper plugin initialization
- **Dependency Resolution** - Support for plugin dependencies
- **Hot Reloading** - Ability to reload plugins during development
- **Hook System** - Event-driven plugin communication

## 📦 Creating Plugins

### Basic Plugin Structure

A WolfPy plugin is a Python package with a specific structure:

```
myplugin/
├── __init__.py          # Main plugin module
├── plugin.toml          # Plugin metadata (optional)
├── routes.py           # Plugin routes (optional)
├── models.py           # Plugin models (optional)
├── templates/          # Plugin templates (optional)
└── static/            # Plugin static files (optional)
```

### Plugin Entry Point

Every plugin must have a `setup` function that receives the WolfPy app instance:

```python
# myplugin/__init__.py
"""
My Custom Plugin for WolfPy

This plugin adds custom functionality to WolfPy applications.
"""

def setup(app):
    """
    Setup plugin with WolfPy app.
    
    Args:
        app: WolfPy application instance
    """
    print(f"🔌 Loading {__name__} plugin...")
    
    # Register routes
    @app.route('/myplugin')
    def plugin_home(request):
        return "Hello from My Plugin!"
    
    @app.route('/myplugin/api/data')
    def plugin_api(request):
        return app.response.json({
            'plugin': 'myplugin',
            'status': 'active',
            'data': get_plugin_data()
        })
    
    # Register middleware (optional)
    from .middleware import MyPluginMiddleware
    app.add_middleware(MyPluginMiddleware())
    
    # Initialize plugin resources
    initialize_plugin_resources(app)
    
    return True  # Return True to indicate successful setup

def teardown(app):
    """
    Cleanup plugin resources.
    
    Args:
        app: WolfPy application instance
    """
    print(f"🔌 Unloading {__name__} plugin...")
    cleanup_plugin_resources(app)

def get_plugin_data():
    """Get plugin-specific data."""
    return {
        'version': '1.0.0',
        'features': ['custom_routes', 'api_endpoints', 'middleware']
    }

def initialize_plugin_resources(app):
    """Initialize plugin resources."""
    # Create database tables, load configuration, etc.
    pass

def cleanup_plugin_resources(app):
    """Cleanup plugin resources."""
    # Close connections, cleanup temporary files, etc.
    pass
```

### Plugin Metadata

Create a `plugin.toml` file to provide metadata about your plugin:

```toml
[plugin]
name = "myplugin"
version = "1.0.0"
description = "My custom WolfPy plugin"
author = "Your Name"
email = "your.email@example.com"
license = "MIT"
homepage = "https://github.com/yourusername/myplugin"

[plugin.dependencies]
wolfpy = ">=0.1.0"
requests = ">=2.25.0"

[plugin.entry_points]
wolfpy_plugins = "myplugin:setup"
```

## 🚀 Installing Plugins

### Method 1: Entry Points (Recommended)

For distributable plugins, use Python's entry points system. Add this to your plugin's `setup.py` or `pyproject.toml`:

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="wolfpy-myplugin",
    version="1.0.0",
    packages=find_packages(),
    entry_points={
        'wolfpy.plugins': [
            'myplugin = myplugin:setup',
        ],
    },
    install_requires=[
        'wolfpy>=0.1.0',
    ],
)
```

Or in `pyproject.toml`:

```toml
[project.entry-points."wolfpy.plugins"]
myplugin = "myplugin:setup"
```

Install the plugin:

```bash
pip install wolfpy-myplugin
```

### Method 2: Local Plugins

For development or private plugins, place them in a `plugins/` directory:

```
myproject/
├── app.py
├── plugins/
│   └── myplugin/
│       ├── __init__.py
│       └── plugin.toml
└── requirements.txt
```

## 🔧 Using Plugins

### Loading Plugins in Your Application

```python
from wolfpy import WolfPy

app = WolfPy()

# Method 1: Load all discovered plugins
app.plugin_manager.load_all_plugins()

# Method 2: Load specific plugins
app.plugin_manager.load_plugin('myplugin')
app.plugin_manager.load_plugin('anotherplugin')

# Method 3: Load plugins with error handling
plugins_to_load = ['myplugin', 'anotherplugin']
for plugin_name in plugins_to_load:
    try:
        if app.plugin_manager.load_plugin(plugin_name):
            print(f"✅ Loaded plugin: {plugin_name}")
        else:
            print(f"❌ Failed to load plugin: {plugin_name}")
    except Exception as e:
        print(f"❌ Error loading plugin {plugin_name}: {e}")
```

### Plugin Management

```python
# Get information about loaded plugins
loaded_plugins = app.plugin_manager.get_loaded_plugins()
for plugin in loaded_plugins:
    print(f"Plugin: {plugin.name} v{plugin.version}")

# Get specific plugin info
plugin_info = app.plugin_manager.get_plugin_info('myplugin')
if plugin_info:
    print(f"Description: {plugin_info.description}")

# Unload a plugin
app.plugin_manager.unload_plugin('myplugin')

# Reload a plugin (useful for development)
app.plugin_manager.reload_plugin('myplugin')
```

## 🎣 Plugin Hooks

WolfPy provides a hook system for plugin communication:

```python
# In your plugin
def setup(app):
    # Register hook callbacks
    app.plugin_manager.register_hook('before_request', on_before_request)
    app.plugin_manager.register_hook('after_response', on_after_response)

def on_before_request(request):
    """Called before each request."""
    print(f"Plugin processing request: {request.path}")

def on_after_response(request, response):
    """Called after each response."""
    print(f"Plugin processed response: {response.status_code}")

# In your application
@app.before_request
def call_plugin_hooks(request):
    app.plugin_manager.call_hook('before_request', request)

@app.after_request
def call_plugin_hooks(request, response):
    app.plugin_manager.call_hook('after_response', request, response)
```

## 🛠️ CLI Plugin Management

Use the WolfPy CLI to manage plugins:

```bash
# List installed plugins
wolfpy plugin list

# Install a plugin
wolfpy plugin install myplugin

# Remove a plugin
wolfpy plugin remove myplugin

# Get plugin information
wolfpy plugin info myplugin

# Create a new plugin template
wolfpy plugin create newplugin
```

## 🔍 Plugin Discovery

WolfPy automatically discovers plugins using multiple methods:

1. **Entry Points** - Standard Python package entry points
2. **Local Directories** - Plugins in `plugins/` directory
3. **Environment Variables** - `WOLFPY_PLUGINS_PATH`

```python
# Discover all available plugins
discovered = app.plugin_manager.discover_plugins()
for plugin in discovered:
    print(f"Found plugin: {plugin.name} ({plugin.version})")
```

## 📝 Best Practices

### Plugin Development

1. **Use descriptive names** - Choose clear, unique plugin names
2. **Handle errors gracefully** - Don't crash the main application
3. **Clean up resources** - Implement proper teardown functions
4. **Document your plugin** - Provide clear documentation and examples
5. **Version your plugin** - Use semantic versioning
6. **Test thoroughly** - Include comprehensive tests

### Plugin Security

1. **Validate inputs** - Always validate data from the main application
2. **Limit permissions** - Only request necessary permissions
3. **Sanitize outputs** - Clean data before returning to the application
4. **Use secure dependencies** - Keep dependencies up to date

### Performance Considerations

1. **Lazy loading** - Load resources only when needed
2. **Cache data** - Cache expensive operations
3. **Minimize startup time** - Keep setup functions fast
4. **Profile your plugin** - Monitor performance impact

## 🧪 Testing Plugins

```python
import pytest
from wolfpy import WolfPy
from wolfpy.testing import TestClient

def test_plugin_loading():
    app = WolfPy()
    assert app.plugin_manager.load_plugin('myplugin')
    
    loaded_plugins = app.plugin_manager.get_loaded_plugins()
    plugin_names = [p.name for p in loaded_plugins]
    assert 'myplugin' in plugin_names

def test_plugin_routes():
    app = WolfPy()
    app.plugin_manager.load_plugin('myplugin')
    
    client = TestClient(app)
    response = client.get('/myplugin')
    assert response.status_code == 200
    assert 'Hello from My Plugin!' in response.text

def test_plugin_api():
    app = WolfPy()
    app.plugin_manager.load_plugin('myplugin')
    
    client = TestClient(app)
    response = client.get('/myplugin/api/data')
    assert response.status_code == 200
    
    data = response.json()
    assert data['plugin'] == 'myplugin'
    assert data['status'] == 'active'
```

## 📚 Example Plugins

Check out these example plugins for inspiration:

- **wolfpy-auth** - Enhanced authentication plugin
- **wolfpy-admin** - Admin interface plugin
- **wolfpy-cache** - Advanced caching plugin
- **wolfpy-monitoring** - Application monitoring plugin

## 🤝 Contributing Plugins

Want to share your plugin with the community? Here's how:

1. Create a GitHub repository for your plugin
2. Follow the naming convention: `wolfpy-pluginname`
3. Include comprehensive documentation
4. Add tests and CI/CD
5. Publish to PyPI
6. Submit to the WolfPy plugin registry

---

The plugin system makes WolfPy incredibly extensible. Start building your own plugins today! 🚀
