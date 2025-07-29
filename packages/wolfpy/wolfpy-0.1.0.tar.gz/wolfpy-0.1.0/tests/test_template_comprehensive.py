"""
Comprehensive unit tests for WolfPy Template Engine.

This test suite covers all aspects of template processing including:
- Template loading and caching
- Variable substitution and context handling
- Control structures (if, for, include)
- Template inheritance and blocks
- Custom filters and functions
- Error handling and debugging
- Security features (auto-escaping)
- Performance optimization
"""

import pytest
import tempfile
import os
from unittest.mock import MagicMock, patch

from src.wolfpy.core.template import TemplateEngine, Template, TemplateLoader, TemplateContext


class TestTemplateEngine:
    """Test template engine functionality."""
    
    def test_engine_initialization(self):
        """Test template engine initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = TemplateEngine(template_dir=temp_dir)
            
            assert engine.template_dir == temp_dir
            assert engine.auto_escape is True
            assert engine.enable_caching is True
            assert isinstance(engine.loader, TemplateLoader)
    
    def test_engine_with_custom_settings(self):
        """Test template engine with custom settings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = TemplateEngine(
                template_dir=temp_dir,
                auto_escape=False,
                enable_caching=False
            )
            
            assert engine.auto_escape is False
            assert engine.enable_caching is False
    
    def test_render_simple_template(self):
        """Test rendering a simple template."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create template file
            template_path = os.path.join(temp_dir, 'hello.html')
            with open(template_path, 'w') as f:
                f.write('<h1>Hello {{ name }}!</h1>')
            
            engine = TemplateEngine(template_dir=temp_dir)
            result = engine.render('hello.html', {'name': 'World'})
            
            assert result == '<h1>Hello World!</h1>'
    
    def test_render_template_with_context(self):
        """Test rendering template with complex context."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create template file
            template_path = os.path.join(temp_dir, 'user.html')
            with open(template_path, 'w') as f:
                f.write('''
                <div class="user">
                    <h2>{{ user.name }}</h2>
                    <p>Age: {{ user.age }}</p>
                    <p>Email: {{ user.email }}</p>
                </div>
                ''')
            
            engine = TemplateEngine(template_dir=temp_dir)
            context = {
                'user': {
                    'name': 'John Doe',
                    'age': 30,
                    'email': 'john@example.com'
                }
            }
            result = engine.render('user.html', context)
            
            assert 'John Doe' in result
            assert '30' in result
            assert 'john@example.com' in result


class TestTemplateVariables:
    """Test template variable handling."""
    
    def test_simple_variable_substitution(self):
        """Test simple variable substitution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = os.path.join(temp_dir, 'test.html')
            with open(template_path, 'w') as f:
                f.write('Hello {{ name }}!')
            
            engine = TemplateEngine(template_dir=temp_dir)
            result = engine.render('test.html', {'name': 'Alice'})
            
            assert result == 'Hello Alice!'
    
    def test_nested_variable_access(self):
        """Test accessing nested variables."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = os.path.join(temp_dir, 'test.html')
            with open(template_path, 'w') as f:
                f.write('{{ user.profile.name }}')
            
            engine = TemplateEngine(template_dir=temp_dir)
            context = {
                'user': {
                    'profile': {
                        'name': 'Bob Smith'
                    }
                }
            }
            result = engine.render('test.html', context)
            
            assert result == 'Bob Smith'
    
    def test_missing_variable(self):
        """Test handling of missing variables."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = os.path.join(temp_dir, 'test.html')
            with open(template_path, 'w') as f:
                f.write('Hello {{ missing_var }}!')
            
            engine = TemplateEngine(template_dir=temp_dir)
            result = engine.render('test.html', {})
            
            # Should render empty string for missing variables
            assert result == 'Hello !'
    
    def test_variable_with_default(self):
        """Test variable with default value."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = os.path.join(temp_dir, 'test.html')
            with open(template_path, 'w') as f:
                f.write('Hello {{ name|default:"Anonymous" }}!')
            
            engine = TemplateEngine(template_dir=temp_dir)
            
            # Test with value
            result1 = engine.render('test.html', {'name': 'Alice'})
            assert result1 == 'Hello Alice!'
            
            # Test without value (should use default)
            result2 = engine.render('test.html', {})
            assert result2 == 'Hello Anonymous!'


class TestTemplateControlStructures:
    """Test template control structures."""
    
    def test_if_statement(self):
        """Test if statement in templates."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = os.path.join(temp_dir, 'test.html')
            with open(template_path, 'w') as f:
                f.write('''
                {% if user_logged_in %}
                    <p>Welcome back!</p>
                {% else %}
                    <p>Please log in.</p>
                {% endif %}
                ''')
            
            engine = TemplateEngine(template_dir=temp_dir)
            
            # Test with condition true
            result1 = engine.render('test.html', {'user_logged_in': True})
            assert 'Welcome back!' in result1
            assert 'Please log in.' not in result1
            
            # Test with condition false
            result2 = engine.render('test.html', {'user_logged_in': False})
            assert 'Welcome back!' not in result2
            assert 'Please log in.' in result2
    
    def test_for_loop(self):
        """Test for loop in templates."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = os.path.join(temp_dir, 'test.html')
            with open(template_path, 'w') as f:
                f.write('''
                <ul>
                {% for item in items %}
                    <li>{{ item }}</li>
                {% endfor %}
                </ul>
                ''')
            
            engine = TemplateEngine(template_dir=temp_dir)
            context = {'items': ['Apple', 'Banana', 'Cherry']}
            result = engine.render('test.html', context)
            
            assert '<li>Apple</li>' in result
            assert '<li>Banana</li>' in result
            assert '<li>Cherry</li>' in result
    
    def test_for_loop_with_objects(self):
        """Test for loop with object iteration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = os.path.join(temp_dir, 'test.html')
            with open(template_path, 'w') as f:
                f.write('''
                {% for user in users %}
                    <div>{{ user.name }} - {{ user.email }}</div>
                {% endfor %}
                ''')
            
            engine = TemplateEngine(template_dir=temp_dir)
            context = {
                'users': [
                    {'name': 'Alice', 'email': 'alice@example.com'},
                    {'name': 'Bob', 'email': 'bob@example.com'}
                ]
            }
            result = engine.render('test.html', context)
            
            assert 'Alice - alice@example.com' in result
            assert 'Bob - bob@example.com' in result
    
    def test_nested_control_structures(self):
        """Test nested control structures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = os.path.join(temp_dir, 'test.html')
            with open(template_path, 'w') as f:
                f.write('''
                {% for category in categories %}
                    <h3>{{ category.name }}</h3>
                    {% if category.items %}
                        <ul>
                        {% for item in category.items %}
                            <li>{{ item }}</li>
                        {% endfor %}
                        </ul>
                    {% else %}
                        <p>No items in this category.</p>
                    {% endif %}
                {% endfor %}
                ''')
            
            engine = TemplateEngine(template_dir=temp_dir)
            context = {
                'categories': [
                    {'name': 'Fruits', 'items': ['Apple', 'Banana']},
                    {'name': 'Vegetables', 'items': []},
                ]
            }
            result = engine.render('test.html', context)
            
            assert 'Fruits' in result
            assert 'Apple' in result
            assert 'Banana' in result
            assert 'Vegetables' in result
            assert 'No items in this category.' in result


class TestTemplateInheritance:
    """Test template inheritance functionality."""
    
    def test_template_extends(self):
        """Test template inheritance with extends."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create base template
            base_path = os.path.join(temp_dir, 'base.html')
            with open(base_path, 'w') as f:
                f.write('''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>{% block title %}Default Title{% endblock %}</title>
                </head>
                <body>
                    <header>
                        <h1>My Website</h1>
                    </header>
                    <main>
                        {% block content %}{% endblock %}
                    </main>
                </body>
                </html>
                ''')
            
            # Create child template
            child_path = os.path.join(temp_dir, 'page.html')
            with open(child_path, 'w') as f:
                f.write('''
                {% extends "base.html" %}
                
                {% block title %}Page Title{% endblock %}
                
                {% block content %}
                    <p>This is the page content.</p>
                {% endblock %}
                ''')
            
            engine = TemplateEngine(template_dir=temp_dir)
            result = engine.render('page.html', {})
            
            assert '<title>Page Title</title>' in result
            assert '<h1>My Website</h1>' in result
            assert '<p>This is the page content.</p>' in result
    
    def test_template_include(self):
        """Test template inclusion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create partial template
            partial_path = os.path.join(temp_dir, 'header.html')
            with open(partial_path, 'w') as f:
                f.write('<header><h1>{{ site_name }}</h1></header>')
            
            # Create main template
            main_path = os.path.join(temp_dir, 'main.html')
            with open(main_path, 'w') as f:
                f.write('''
                <!DOCTYPE html>
                <html>
                <body>
                    {% include "header.html" %}
                    <main>Content goes here</main>
                </body>
                </html>
                ''')
            
            engine = TemplateEngine(template_dir=temp_dir)
            result = engine.render('main.html', {'site_name': 'My Site'})
            
            assert '<h1>My Site</h1>' in result
            assert '<main>Content goes here</main>' in result


class TestTemplateFilters:
    """Test template filter functionality."""
    
    def test_built_in_filters(self):
        """Test built-in template filters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = os.path.join(temp_dir, 'test.html')
            with open(template_path, 'w') as f:
                f.write('''
                <p>{{ name|upper }}</p>
                <p>{{ description|truncate:50 }}</p>
                <p>{{ count|default:0 }}</p>
                <p>{{ html_content|safe }}</p>
                ''')
            
            engine = TemplateEngine(template_dir=temp_dir)
            context = {
                'name': 'john doe',
                'description': 'This is a very long description that should be truncated',
                'html_content': '<strong>Bold text</strong>'
            }
            result = engine.render('test.html', context)
            
            assert 'JOHN DOE' in result
            assert len([line for line in result.split('\n') if 'truncated' in line]) > 0
            assert '<strong>Bold text</strong>' in result
    
    def test_custom_filter(self):
        """Test custom template filter."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = os.path.join(temp_dir, 'test.html')
            with open(template_path, 'w') as f:
                f.write('{{ text|reverse }}')
            
            engine = TemplateEngine(template_dir=temp_dir)
            
            # Register custom filter
            def reverse_filter(value):
                return value[::-1]
            
            engine.add_filter('reverse', reverse_filter)
            
            result = engine.render('test.html', {'text': 'hello'})
            assert result == 'olleh'


class TestTemplateErrorHandling:
    """Test template error handling."""
    
    def test_template_not_found(self):
        """Test handling of missing template files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = TemplateEngine(template_dir=temp_dir)
            
            with pytest.raises(FileNotFoundError):
                engine.render('nonexistent.html', {})
    
    def test_template_syntax_error(self):
        """Test handling of template syntax errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = os.path.join(temp_dir, 'bad.html')
            with open(template_path, 'w') as f:
                f.write('{{ unclosed_variable')
            
            engine = TemplateEngine(template_dir=temp_dir)
            
            with pytest.raises(Exception):  # Should raise template syntax error
                engine.render('bad.html', {})
    
    def test_template_runtime_error(self):
        """Test handling of template runtime errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = os.path.join(temp_dir, 'error.html')
            with open(template_path, 'w') as f:
                f.write('{{ user.nonexistent.property }}')
            
            engine = TemplateEngine(template_dir=temp_dir)
            
            # Should handle gracefully and not crash
            result = engine.render('error.html', {'user': {}})
            assert result is not None


class TestTemplateSecurity:
    """Test template security features."""
    
    def test_auto_escape_enabled(self):
        """Test auto-escaping of HTML content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = os.path.join(temp_dir, 'test.html')
            with open(template_path, 'w') as f:
                f.write('{{ user_input }}')
            
            engine = TemplateEngine(template_dir=temp_dir, auto_escape=True)
            context = {'user_input': '<script>alert("XSS")</script>'}
            result = engine.render('test.html', context)
            
            # Should escape HTML
            assert '&lt;script&gt;' in result
            assert '<script>' not in result
    
    def test_auto_escape_disabled(self):
        """Test with auto-escaping disabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = os.path.join(temp_dir, 'test.html')
            with open(template_path, 'w') as f:
                f.write('{{ user_input }}')
            
            engine = TemplateEngine(template_dir=temp_dir, auto_escape=False)
            context = {'user_input': '<strong>Bold</strong>'}
            result = engine.render('test.html', context)
            
            # Should not escape HTML
            assert '<strong>Bold</strong>' in result
    
    def test_safe_filter(self):
        """Test safe filter to bypass auto-escaping."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = os.path.join(temp_dir, 'test.html')
            with open(template_path, 'w') as f:
                f.write('{{ html_content|safe }}')
            
            engine = TemplateEngine(template_dir=temp_dir, auto_escape=True)
            context = {'html_content': '<em>Emphasized</em>'}
            result = engine.render('test.html', context)
            
            # Should not escape when using safe filter
            assert '<em>Emphasized</em>' in result


class TestTemplateCaching:
    """Test template caching functionality."""
    
    def test_template_caching_enabled(self):
        """Test that template caching works when enabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = os.path.join(temp_dir, 'test.html')
            with open(template_path, 'w') as f:
                f.write('Hello {{ name }}!')
            
            engine = TemplateEngine(template_dir=temp_dir, enable_caching=True)
            
            # First render should cache the template
            result1 = engine.render('test.html', {'name': 'World'})
            assert result1 == 'Hello World!'
            
            # Second render should use cached template
            result2 = engine.render('test.html', {'name': 'Alice'})
            assert result2 == 'Hello Alice!'
            
            # Check that template is in cache
            assert 'test.html' in engine.template_cache
    
    def test_template_caching_disabled(self):
        """Test that template caching can be disabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = os.path.join(temp_dir, 'test.html')
            with open(template_path, 'w') as f:
                f.write('Hello {{ name }}!')
            
            engine = TemplateEngine(template_dir=temp_dir, enable_caching=False)
            
            # Render template
            result = engine.render('test.html', {'name': 'World'})
            assert result == 'Hello World!'
            
            # Check that template is not cached
            assert len(engine.template_cache) == 0


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
