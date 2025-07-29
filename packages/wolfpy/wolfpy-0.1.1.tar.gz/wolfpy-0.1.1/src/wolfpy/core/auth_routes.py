"""
FoxPy Authentication Routes Module.

This module provides ready-to-use authentication route handlers for
login, logout, registration, and user management.
"""

import json
from typing import Dict, Any, Optional
from .auth import Auth, User, PasswordHasher, anonymous_required, login_required
from .request import Request
from .response import Response


class AuthRoutes:
    """
    Authentication route handlers for FoxPy applications.
    
    Provides ready-to-use routes for user authentication including
    login, logout, registration, and profile management.
    """
    
    def __init__(self, auth: Auth, template_engine=None):
        """
        Initialize authentication routes.
        
        Args:
            auth: Auth manager instance
            template_engine: Template engine for rendering forms
        """
        self.auth = auth
        self.template_engine = template_engine
    
    def register_routes(self, app):
        """
        Register authentication routes with the application.
        
        Args:
            app: FoxPy application instance
        """
        # Registration routes
        app.route('/register', methods=['GET', 'POST'])(
            anonymous_required('/dashboard')(self.register)
        )
        
        # Login routes
        app.route('/login', methods=['GET', 'POST'])(
            anonymous_required('/dashboard')(self.login)
        )
        
        # Logout route
        app.route('/logout', methods=['GET', 'POST'])(self.logout)
        
        # Profile routes
        app.route('/profile', methods=['GET'])(
            login_required()(self.profile)
        )
        app.route('/profile/edit', methods=['GET', 'POST'])(
            login_required()(self.edit_profile)
        )
        
        # API routes
        app.route('/api/auth/register', methods=['POST'])(self.api_register)
        app.route('/api/auth/login', methods=['POST'])(self.api_login)
        app.route('/api/auth/logout', methods=['POST'])(self.api_logout)
        app.route('/api/auth/me', methods=['GET'])(login_required()(self.api_me))
    
    def register(self, request: Request) -> Response:
        """
        Handle user registration.
        
        Args:
            request: HTTP request
            
        Returns:
            Registration form or redirect after successful registration
        """
        if request.method == 'GET':
            # Show registration form
            if self.template_engine:
                context = {
                    'title': 'Register',
                    'csrf_token': request.get_context('csrf_token', '')
                }
                return Response(self.template_engine.render('auth/register.html', context))
            else:
                # Return basic HTML form
                return Response(self._get_register_form_html(request))
        
        # Handle POST request
        username = request.get_form('username', '').strip()
        email = request.get_form('email', '').strip()
        password = request.get_form('password', '')
        confirm_password = request.get_form('confirm_password', '')
        
        # Validation
        errors = []
        
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters long')
        
        if not email or '@' not in email:
            errors.append('Valid email address is required')
        
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long')
        
        if password != confirm_password:
            errors.append('Passwords do not match')
        
        # Check if username already exists
        existing_user = None
        for user in self.auth.users.values():
            if user.username == username:
                existing_user = user
                break
        
        if existing_user:
            errors.append('Username already exists')
        
        if errors:
            if self.template_engine:
                context = {
                    'title': 'Register',
                    'errors': errors,
                    'username': username,
                    'email': email,
                    'csrf_token': request.get_context('csrf_token', '')
                }
                return Response(self.template_engine.render('auth/register.html', context))
            else:
                return Response(self._get_register_form_html(request, errors, username, email))
        
        # Create user
        try:
            user = self.auth.create_user(username, password, email)
            
            # Log in the user
            self.auth.login_user_session(user, request)
            
            # Set success message in session
            if hasattr(request, 'session'):
                request.session['flash_message'] = f'Welcome, {username}! Your account has been created.'
            
            return Response.redirect('/dashboard')
            
        except Exception as e:
            errors.append(f'Registration failed: {str(e)}')
            if self.template_engine:
                context = {
                    'title': 'Register',
                    'errors': errors,
                    'username': username,
                    'email': email,
                    'csrf_token': request.get_context('csrf_token', '')
                }
                return Response(self.template_engine.render('auth/register.html', context))
            else:
                return Response(self._get_register_form_html(request, errors, username, email))
    
    def login(self, request: Request) -> Response:
        """
        Handle user login.
        
        Args:
            request: HTTP request
            
        Returns:
            Login form or redirect after successful login
        """
        if request.method == 'GET':
            # Show login form
            if self.template_engine:
                context = {
                    'title': 'Login',
                    'csrf_token': request.get_context('csrf_token', '')
                }
                return Response(self.template_engine.render('auth/login.html', context))
            else:
                # Return basic HTML form
                return Response(self._get_login_form_html(request))
        
        # Handle POST request
        username = request.get_form('username', '').strip()
        password = request.get_form('password', '')
        remember = request.get_form('remember') == 'on'
        
        # Validation
        errors = []
        
        if not username:
            errors.append('Username is required')
        
        if not password:
            errors.append('Password is required')
        
        if not errors:
            # Attempt authentication
            user = self.auth.authenticate(username, password)
            
            if user:
                # Log in the user
                self.auth.login_user_session(user, request, remember)
                
                # Set success message in session
                if hasattr(request, 'session'):
                    request.session['flash_message'] = f'Welcome back, {user.username}!'
                
                # Redirect to next page or dashboard
                next_url = request.get_arg('next', '/dashboard')
                return Response.redirect(next_url)
            else:
                errors.append('Invalid username or password')
        
        # Show form with errors
        if self.template_engine:
            context = {
                'title': 'Login',
                'errors': errors,
                'username': username,
                'csrf_token': request.get_context('csrf_token', '')
            }
            return Response(self.template_engine.render('auth/login.html', context))
        else:
            return Response(self._get_login_form_html(request, errors, username))
    
    def logout(self, request: Request) -> Response:
        """
        Handle user logout.
        
        Args:
            request: HTTP request
            
        Returns:
            Redirect to home page
        """
        # Log out the user
        self.auth.logout_user_session(request)
        
        # Set success message in session
        if hasattr(request, 'session'):
            request.session['flash_message'] = 'You have been logged out successfully.'
        
        return Response.redirect('/')
    
    def profile(self, request: Request) -> Response:
        """
        Show user profile.
        
        Args:
            request: HTTP request
            
        Returns:
            User profile page
        """
        user = request.user
        
        if self.template_engine:
            context = {
                'title': 'Profile',
                'user': user.to_dict(),
                'csrf_token': request.get_context('csrf_token', '')
            }
            return Response(self.template_engine.render('auth/profile.html', context))
        else:
            # Return basic profile info
            return Response(f"""
            <html>
            <head><title>Profile</title></head>
            <body>
                <h1>User Profile</h1>
                <p><strong>Username:</strong> {user.username}</p>
                <p><strong>Email:</strong> {user.email or 'Not provided'}</p>
                <p><strong>User ID:</strong> {user.id}</p>
                <a href="/profile/edit">Edit Profile</a> |
                <a href="/logout">Logout</a>
            </body>
            </html>
            """)
    
    def edit_profile(self, request: Request) -> Response:
        """
        Handle profile editing.
        
        Args:
            request: HTTP request
            
        Returns:
            Profile edit form or redirect after successful update
        """
        user = request.user
        
        if request.method == 'GET':
            # Show edit form
            if self.template_engine:
                context = {
                    'title': 'Edit Profile',
                    'user': user.to_dict(),
                    'csrf_token': request.get_context('csrf_token', '')
                }
                return Response(self.template_engine.render('auth/edit_profile.html', context))
            else:
                # Return basic edit form
                return Response(self._get_edit_profile_form_html(request, user))
        
        # Handle POST request
        email = request.get_form('email', '').strip()
        current_password = request.get_form('current_password', '')
        new_password = request.get_form('new_password', '')
        confirm_password = request.get_form('confirm_password', '')
        
        errors = []
        
        # Validate email
        if email and '@' not in email:
            errors.append('Valid email address is required')
        
        # Validate password change
        if new_password:
            if not current_password:
                errors.append('Current password is required to change password')
            elif not self.auth.authenticate(user.username, current_password):
                errors.append('Current password is incorrect')
            elif len(new_password) < 6:
                errors.append('New password must be at least 6 characters long')
            elif new_password != confirm_password:
                errors.append('New passwords do not match')
        
        if not errors:
            # Update user
            if email:
                user.email = email
            
            if new_password:
                user.set('password_hash', PasswordHasher.hash_password(new_password))
            
            # Set success message
            if hasattr(request, 'session'):
                request.session['flash_message'] = 'Profile updated successfully!'
            
            return Response.redirect('/profile')
        
        # Show form with errors
        if self.template_engine:
            context = {
                'title': 'Edit Profile',
                'user': user.to_dict(),
                'errors': errors,
                'email': email,
                'csrf_token': request.get_context('csrf_token', '')
            }
            return Response(self.template_engine.render('auth/edit_profile.html', context))
        else:
            return Response(self._get_edit_profile_form_html(request, user, errors, email))
    
    # API endpoints
    def api_register(self, request: Request) -> Response:
        """API endpoint for user registration."""
        try:
            data = request.json
            username = data.get('username', '').strip()
            email = data.get('email', '').strip()
            password = data.get('password', '')
            
            # Validation
            if not username or len(username) < 3:
                return Response.bad_request({'error': 'Username must be at least 3 characters long'})
            
            if not email or '@' not in email:
                return Response.bad_request({'error': 'Valid email address is required'})
            
            if not password or len(password) < 6:
                return Response.bad_request({'error': 'Password must be at least 6 characters long'})
            
            # Check if username exists
            for user in self.auth.users.values():
                if user.username == username:
                    return Response.bad_request({'error': 'Username already exists'})
            
            # Create user
            user = self.auth.create_user(username, password, email)
            
            # Create token
            token = self.auth.login_user(user)
            
            return Response.json({
                'success': True,
                'message': 'User registered successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                },
                'token': token
            }, status=201)
            
        except Exception as e:
            return Response.server_error({'error': f'Registration failed: {str(e)}'})
    
    def api_login(self, request: Request) -> Response:
        """API endpoint for user login."""
        try:
            data = request.json
            username = data.get('username', '').strip()
            password = data.get('password', '')
            remember = data.get('remember', False)
            
            if not username or not password:
                return Response.bad_request({'error': 'Username and password are required'})
            
            # Authenticate user
            user = self.auth.authenticate(username, password)
            
            if not user:
                return Response.unauthorized({'error': 'Invalid username or password'})
            
            # Create token
            token = self.auth.login_user(user, remember)
            
            return Response.json({
                'success': True,
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                },
                'token': token
            })
            
        except Exception as e:
            return Response.server_error({'error': f'Login failed: {str(e)}'})
    
    def api_logout(self, request: Request) -> Response:
        """API endpoint for user logout."""
        # For token-based auth, client should discard the token
        # For session-based auth, clear the session
        if hasattr(request, 'session'):
            request.session.clear()
        
        return Response.json({
            'success': True,
            'message': 'Logout successful'
        })
    
    def api_me(self, request: Request) -> Response:
        """API endpoint to get current user info."""
        user = request.user
        
        return Response.json({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'attributes': user.attributes
            }
        })
    
    # Helper methods for basic HTML forms
    def _get_register_form_html(self, request: Request, errors: list = None, username: str = '', email: str = '') -> str:
        """Generate basic registration form HTML."""
        error_html = ''
        if errors:
            error_html = '<div style="color: red;"><ul>' + ''.join(f'<li>{error}</li>' for error in errors) + '</ul></div>'
        
        csrf_token = request.get_context('csrf_token', '')
        
        return f"""
        <html>
        <head><title>Register</title></head>
        <body>
            <h1>Register</h1>
            {error_html}
            <form method="post">
                <input type="hidden" name="csrf_token" value="{csrf_token}">
                <p>
                    <label>Username:</label><br>
                    <input type="text" name="username" value="{username}" required>
                </p>
                <p>
                    <label>Email:</label><br>
                    <input type="email" name="email" value="{email}" required>
                </p>
                <p>
                    <label>Password:</label><br>
                    <input type="password" name="password" required>
                </p>
                <p>
                    <label>Confirm Password:</label><br>
                    <input type="password" name="confirm_password" required>
                </p>
                <p>
                    <button type="submit">Register</button>
                </p>
            </form>
            <p><a href="/login">Already have an account? Login</a></p>
        </body>
        </html>
        """
    
    def _get_login_form_html(self, request: Request, errors: list = None, username: str = '') -> str:
        """Generate basic login form HTML."""
        error_html = ''
        if errors:
            error_html = '<div style="color: red;"><ul>' + ''.join(f'<li>{error}</li>' for error in errors) + '</ul></div>'
        
        csrf_token = request.get_context('csrf_token', '')
        
        return f"""
        <html>
        <head><title>Login</title></head>
        <body>
            <h1>Login</h1>
            {error_html}
            <form method="post">
                <input type="hidden" name="csrf_token" value="{csrf_token}">
                <p>
                    <label>Username:</label><br>
                    <input type="text" name="username" value="{username}" required>
                </p>
                <p>
                    <label>Password:</label><br>
                    <input type="password" name="password" required>
                </p>
                <p>
                    <label>
                        <input type="checkbox" name="remember"> Remember me
                    </label>
                </p>
                <p>
                    <button type="submit">Login</button>
                </p>
            </form>
            <p><a href="/register">Don't have an account? Register</a></p>
        </body>
        </html>
        """
    
    def _get_edit_profile_form_html(self, request: Request, user: User, errors: list = None, email: str = '') -> str:
        """Generate basic edit profile form HTML."""
        error_html = ''
        if errors:
            error_html = '<div style="color: red;"><ul>' + ''.join(f'<li>{error}</li>' for error in errors) + '</ul></div>'
        
        csrf_token = request.get_context('csrf_token', '')
        current_email = email or user.email or ''
        
        return f"""
        <html>
        <head><title>Edit Profile</title></head>
        <body>
            <h1>Edit Profile</h1>
            {error_html}
            <form method="post">
                <input type="hidden" name="csrf_token" value="{csrf_token}">
                <p>
                    <label>Username:</label><br>
                    <input type="text" value="{user.username}" disabled>
                    <small>(Username cannot be changed)</small>
                </p>
                <p>
                    <label>Email:</label><br>
                    <input type="email" name="email" value="{current_email}">
                </p>
                <h3>Change Password</h3>
                <p>
                    <label>Current Password:</label><br>
                    <input type="password" name="current_password">
                </p>
                <p>
                    <label>New Password:</label><br>
                    <input type="password" name="new_password">
                </p>
                <p>
                    <label>Confirm New Password:</label><br>
                    <input type="password" name="confirm_password">
                </p>
                <p>
                    <button type="submit">Update Profile</button>
                    <a href="/profile">Cancel</a>
                </p>
            </form>
        </body>
        </html>
        """
