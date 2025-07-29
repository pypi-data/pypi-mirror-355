"""
WolfPy Error Handling Demo Application

This example demonstrates the comprehensive error handling features of WolfPy:
- Custom error pages for different HTTP status codes
- Exception middleware for global error catching
- Pretty error tracebacks in development mode
- Error logging with different levels
- Validation error handling
- Security-aware error responses
"""

import os
import sys
import tempfile
from datetime import datetime

# Add the src directory to the path so we can import wolfpy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from wolfpy import WolfPy, Request, Response
from wolfpy.core.error_handling import ValidationErrorHandler


# Create WolfPy application with error handling enabled
app = WolfPy(
    debug=True,  # Enable debug mode for detailed error pages
    enable_error_logging=True,
    log_file='error_demo.log',
    log_level='DEBUG'
)


@app.route('/')
def home():
    """Home page with links to error examples."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WolfPy Error Handling Demo</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .error-links { background: #f8f9fa; padding: 20px; border-radius: 8px; }
            .error-links a { display: block; margin: 10px 0; padding: 10px; 
                           background: #007bff; color: white; text-decoration: none; 
                           border-radius: 4px; text-align: center; }
            .error-links a:hover { background: #0056b3; }
            .description { margin: 20px 0; line-height: 1.6; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🐺 WolfPy Error Handling Demo</h1>
            
            <div class="description">
                <p>This demo showcases WolfPy's comprehensive error handling system. 
                Click on the links below to see different types of errors and how they're handled:</p>
            </div>
            
            <div class="error-links">
                <h3>Error Examples:</h3>
                <a href="/404-error">404 - Page Not Found</a>
                <a href="/500-error">500 - Internal Server Error</a>
                <a href="/validation-error">422 - Validation Error</a>
                <a href="/custom-error">Custom Error Handler</a>
                <a href="/exception-demo">Exception Handling Demo</a>
                <a href="/logging-demo">Error Logging Demo</a>
            </div>
            
            <div class="description">
                <h3>Features Demonstrated:</h3>
                <ul>
                    <li><strong>Custom Error Pages:</strong> Beautiful, user-friendly error pages</li>
                    <li><strong>Debug Mode:</strong> Detailed tracebacks with syntax highlighting</li>
                    <li><strong>Error Logging:</strong> Comprehensive logging with context information</li>
                    <li><strong>Validation Errors:</strong> Structured validation error handling</li>
                    <li><strong>Security:</strong> Safe error responses that don't leak sensitive information</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """


@app.route('/500-error')
def internal_error():
    """Trigger a 500 internal server error."""
    # This will cause a runtime error
    undefined_variable = some_undefined_variable
    return "This won't be reached"


@app.route('/validation-error')
def validation_error():
    """Demonstrate validation error handling."""
    # Simulate form validation
    errors = {
        'email': ['Invalid email format', 'Email already exists'],
        'password': ['Password too short', 'Password must contain numbers'],
        'username': ['Username is required']
    }
    
    return app.handle_validation_errors(errors, format_type='json')


@app.route('/exception-demo')
def exception_demo():
    """Demonstrate different types of exceptions."""
    error_type = Request.current().get_arg('type', default='runtime')
    
    if error_type == 'value':
        raise ValueError("This is a ValueError example")
    elif error_type == 'type':
        raise TypeError("This is a TypeError example")
    elif error_type == 'key':
        raise KeyError("missing_key")
    elif error_type == 'file':
        raise FileNotFoundError("Template file not found")
    elif error_type == 'permission':
        raise PermissionError("Access denied")
    else:
        # Default runtime error
        raise RuntimeError("This is a RuntimeError example")


@app.route('/logging-demo')
def logging_demo():
    """Demonstrate error logging."""
    request = Request.current()
    
    # Log different types of messages
    app.log_error("This is a test error message", request=request)
    app.log_validation_error('test_field', 'Test validation error', 'invalid_value', request)
    
    return {
        'message': 'Error logging demo completed',
        'check_log_file': 'error_demo.log',
        'timestamp': datetime.now().isoformat()
    }


@app.route('/custom-error')
def custom_error():
    """Trigger a custom error that will be handled by our custom handler."""
    # Create a custom exception
    class CustomBusinessError(Exception):
        pass
    
    raise CustomBusinessError("This is a custom business logic error")


# Register custom error handler
@app.error_handler(404)
def custom_404_handler(error_context):
    """Custom 404 error handler."""
    return Response("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Oops! Page Not Found</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; 
                   background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                   color: white; min-height: 100vh; margin: 0; }
            .error-container { background: rgba(255,255,255,0.1); padding: 40px; 
                             border-radius: 15px; display: inline-block; }
            .error-code { font-size: 120px; font-weight: bold; margin: 0; }
            .error-message { font-size: 24px; margin: 20px 0; }
            .back-link { display: inline-block; padding: 15px 30px; 
                        background: #fff; color: #333; text-decoration: none; 
                        border-radius: 25px; margin-top: 20px; }
            .back-link:hover { background: #f0f0f0; }
        </style>
    </head>
    <body>
        <div class="error-container">
            <div class="error-code">404</div>
            <div class="error-message">Whoops! This page went on vacation 🏖️</div>
            <p>Don't worry, our other pages are still here and ready to help!</p>
            <a href="/" class="back-link">Take Me Home</a>
        </div>
    </body>
    </html>
    """, status=404, headers={'Content-Type': 'text/html'})


# Register custom error handler for our custom exception
def custom_business_error_handler(error_context):
    """Handle custom business errors."""
    return Response.json({
        'error': 'Business Logic Error',
        'message': str(error_context.exception),
        'code': 'CUSTOM_ERROR',
        'timestamp': error_context.timestamp.isoformat(),
        'support_message': 'Please contact support if this error persists.'
    }, status=422)


# Register the custom handler
app.exception_middleware.exception_status_map[type(Exception)] = 422
app.register_error_handler(422, custom_business_error_handler)


@app.route('/api/users', methods=['POST'])
def create_user():
    """API endpoint that demonstrates validation error handling."""
    request = Request.current()
    
    # Simulate validation
    validation_handler = ValidationErrorHandler()
    
    # Check required fields
    if not request.get_json('email'):
        validation_handler.add_error('email', 'Email is required')
    elif '@' not in request.get_json('email', ''):
        validation_handler.add_error('email', 'Invalid email format')
    
    if not request.get_json('password'):
        validation_handler.add_error('password', 'Password is required')
    elif len(request.get_json('password', '')) < 8:
        validation_handler.add_error('password', 'Password must be at least 8 characters')
    
    if not request.get_json('username'):
        validation_handler.add_error('username', 'Username is required')
    
    # If there are validation errors, return them
    if validation_handler.has_errors():
        return validation_handler.to_response(422)
    
    # If validation passes, create user (simulated)
    return Response.json({
        'message': 'User created successfully',
        'user': {
            'id': 123,
            'email': request.get_json('email'),
            'username': request.get_json('username')
        }
    }, status=201)


@app.route('/test-form', methods=['GET', 'POST'])
def test_form():
    """Form for testing validation errors."""
    if Request.current().method == 'GET':
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Form - Validation Demo</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .form-container { max-width: 500px; margin: 0 auto; }
                .form-group { margin: 15px 0; }
                label { display: block; margin-bottom: 5px; font-weight: bold; }
                input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
                button { background: #007bff; color: white; padding: 12px 24px; 
                        border: none; border-radius: 4px; cursor: pointer; }
                button:hover { background: #0056b3; }
                .error { color: #dc3545; font-size: 14px; margin-top: 5px; }
            </style>
        </head>
        <body>
            <div class="form-container">
                <h2>User Registration Form</h2>
                <p>Try submitting with invalid data to see validation errors!</p>
                
                <form method="POST">
                    <div class="form-group">
                        <label for="email">Email:</label>
                        <input type="text" id="email" name="email" placeholder="Enter your email">
                    </div>
                    
                    <div class="form-group">
                        <label for="username">Username:</label>
                        <input type="text" id="username" name="username" placeholder="Enter username">
                    </div>
                    
                    <div class="form-group">
                        <label for="password">Password:</label>
                        <input type="password" id="password" name="password" placeholder="Enter password">
                    </div>
                    
                    <button type="submit">Register</button>
                </form>
                
                <p><a href="/">← Back to Demo Home</a></p>
            </div>
        </body>
        </html>
        """
    else:
        # Handle POST request with validation
        request = Request.current()
        validation_handler = ValidationErrorHandler()
        
        # Validate form data
        email = request.get_form('email')
        username = request.get_form('username')
        password = request.get_form('password')
        
        if not email:
            validation_handler.add_error('email', 'Email is required')
        elif '@' not in email:
            validation_handler.add_error('email', 'Invalid email format')
        
        if not username:
            validation_handler.add_error('username', 'Username is required')
        elif len(username) < 3:
            validation_handler.add_error('username', 'Username must be at least 3 characters')
        
        if not password:
            validation_handler.add_error('password', 'Password is required')
        elif len(password) < 8:
            validation_handler.add_error('password', 'Password must be at least 8 characters')
        
        if validation_handler.has_errors():
            # Return form with errors
            error_html = validation_handler.to_html()
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Validation Errors</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    .container {{ max-width: 600px; margin: 0 auto; }}
                    .validation-errors {{ background: #f8d7da; border: 1px solid #f5c6cb; 
                                        padding: 15px; border-radius: 4px; margin: 20px 0; }}
                    .validation-errors h4 {{ color: #721c24; margin-top: 0; }}
                    .validation-errors ul {{ margin: 10px 0; }}
                    .validation-errors li {{ color: #721c24; }}
                    .back-link {{ display: inline-block; padding: 10px 20px; 
                                background: #007bff; color: white; text-decoration: none; 
                                border-radius: 4px; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Form Validation Failed</h2>
                    {error_html}
                    <a href="/test-form" class="back-link">Try Again</a>
                    <a href="/" class="back-link">Back to Demo</a>
                </div>
            </body>
            </html>
            """
        else:
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Success!</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                    .success { background: #d4edda; border: 1px solid #c3e6cb; 
                             padding: 20px; border-radius: 4px; color: #155724; }
                </style>
            </head>
            <body>
                <div class="success">
                    <h2>Registration Successful!</h2>
                    <p>Your account has been created successfully.</p>
                    <a href="/">Back to Demo Home</a>
                </div>
            </body>
            </html>
            """


if __name__ == '__main__':
    print("🐺 Starting WolfPy Error Handling Demo")
    print("=" * 50)
    print("Visit http://localhost:8000 to see the demo")
    print("Debug mode is enabled - you'll see detailed error pages")
    print("Check 'error_demo.log' for logged errors")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=8000, debug=True)
