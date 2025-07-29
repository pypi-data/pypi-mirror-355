"""
WolfPy Admin System

Django-style admin interface for database models with CRUD operations,
permissions, and a beautiful web interface.
"""

import os
import re
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Type, Callable, Union
from datetime import datetime
from urllib.parse import quote, unquote

from .database import Model, Database, Field, IntegerField, StringField, DateTimeField, BooleanField
from .request import Request
from .response import Response
from .auth import Auth


class AdminUser:
    """Admin user model for authentication."""
    
    def __init__(self, username: str, password_hash: str, email: str = "", 
                 is_superuser: bool = False, permissions: List[str] = None):
        self.username = username
        self.password_hash = password_hash
        self.email = email
        self.is_superuser = is_superuser
        self.permissions = permissions or []
        self.last_login = None
        self.created_at = datetime.now()
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission."""
        if self.is_superuser:
            return True
        return permission in self.permissions
    
    def can_view_model(self, model_name: str) -> bool:
        """Check if user can view a model."""
        return self.has_permission(f"view_{model_name}") or self.has_permission("view_all")
    
    def can_add_model(self, model_name: str) -> bool:
        """Check if user can add instances of a model."""
        return self.has_permission(f"add_{model_name}") or self.has_permission("add_all")
    
    def can_change_model(self, model_name: str) -> bool:
        """Check if user can change instances of a model."""
        return self.has_permission(f"change_{model_name}") or self.has_permission("change_all")
    
    def can_delete_model(self, model_name: str) -> bool:
        """Check if user can delete instances of a model."""
        return self.has_permission(f"delete_{model_name}") or self.has_permission("delete_all")


class ModelAdmin:
    """Configuration for how a model appears in the admin interface."""
    
    def __init__(self, model: Type[Model]):
        self.model = model
        self.list_display = None  # Fields to display in list view
        self.list_filter = None   # Fields to filter by
        self.search_fields = None # Fields to search in
        self.list_per_page = 25   # Items per page
        self.ordering = None      # Default ordering
        self.readonly_fields = None # Read-only fields
        self.exclude = None       # Fields to exclude from forms
        self.fieldsets = None     # Field grouping for forms
        
        # Auto-configure based on model
        self._auto_configure()
    
    def _auto_configure(self):
        """Auto-configure admin based on model fields."""
        fields = list(self.model._fields.keys())
        
        # Default list display (first few fields)
        if not self.list_display:
            self.list_display = fields[:5] if len(fields) > 5 else fields
        
        # Default search fields (string fields)
        if not self.search_fields:
            self.search_fields = [
                name for name, field in self.model._fields.items()
                if isinstance(field, StringField)
            ][:3]  # Limit to 3 fields
        
        # Default list filters (boolean and choice fields)
        if not self.list_filter:
            self.list_filter = [
                name for name, field in self.model._fields.items()
                if isinstance(field, BooleanField)
            ][:3]
        
        # Default ordering (by primary key)
        if not self.ordering:
            pk_field = None
            for name, field in self.model._fields.items():
                if field.primary_key:
                    pk_field = name
                    break
            if pk_field:
                self.ordering = [f"-{pk_field}"]  # Descending order
    
    def get_list_display(self) -> List[str]:
        """Get fields to display in list view."""
        return self.list_display or []
    
    def get_search_fields(self) -> List[str]:
        """Get fields to search in."""
        return self.search_fields or []
    
    def get_list_filter(self) -> List[str]:
        """Get fields to filter by."""
        return self.list_filter or []
    
    def get_queryset(self, request: Request):
        """Get queryset for this model."""
        return self.model.objects.all()
    
    def has_view_permission(self, request: Request, obj=None) -> bool:
        """Check if user has view permission."""
        user = getattr(request, 'admin_user', None)
        if not user:
            return False
        return user.can_view_model(self.model.__name__.lower())
    
    def has_add_permission(self, request: Request) -> bool:
        """Check if user has add permission."""
        user = getattr(request, 'admin_user', None)
        if not user:
            return False
        return user.can_add_model(self.model.__name__.lower())
    
    def has_change_permission(self, request: Request, obj=None) -> bool:
        """Check if user has change permission."""
        user = getattr(request, 'admin_user', None)
        if not user:
            return False
        return user.can_change_model(self.model.__name__.lower())
    
    def has_delete_permission(self, request: Request, obj=None) -> bool:
        """Check if user has delete permission."""
        user = getattr(request, 'admin_user', None)
        if not user:
            return False
        return user.can_delete_model(self.model.__name__.lower())


class AdminSite:
    """
    Main admin site that manages model registration and URL routing.
    """
    
    def __init__(self, name: str = "admin", app_name: str = "admin"):
        self.name = name
        self.app_name = app_name
        self._registry: Dict[Type[Model], ModelAdmin] = {}
        self.admin_users: Dict[str, AdminUser] = {}
        self.site_title = "WolfPy Administration"
        self.site_header = "WolfPy Admin"
        self.index_title = "Site Administration"
        
        # Create default superuser
        self._create_default_superuser()
    
    def _create_default_superuser(self):
        """Create default admin user."""
        # Default admin user (change in production!)
        from .auth import PasswordHasher
        password_hash = PasswordHasher.hash_password("admin123")
        
        self.admin_users["admin"] = AdminUser(
            username="admin",
            password_hash=password_hash,
            email="admin@example.com",
            is_superuser=True
        )
    
    def register(self, model_or_iterable: Union[Type[Model], List[Type[Model]]], 
                 admin_class: Type[ModelAdmin] = None):
        """
        Register model(s) with the admin site.
        
        Args:
            model_or_iterable: Model class or list of model classes
            admin_class: Custom ModelAdmin class
        """
        if not isinstance(model_or_iterable, (list, tuple)):
            model_or_iterable = [model_or_iterable]
        
        for model in model_or_iterable:
            if admin_class:
                admin_instance = admin_class(model)
            else:
                admin_instance = ModelAdmin(model)
            
            self._registry[model] = admin_instance
    
    def unregister(self, model_or_iterable: Union[Type[Model], List[Type[Model]]]):
        """Unregister model(s) from the admin site."""
        if not isinstance(model_or_iterable, (list, tuple)):
            model_or_iterable = [model_or_iterable]
        
        for model in model_or_iterable:
            if model in self._registry:
                del self._registry[model]
    
    def is_registered(self, model: Type[Model]) -> bool:
        """Check if model is registered."""
        return model in self._registry
    
    def get_model_admin(self, model: Type[Model]) -> Optional[ModelAdmin]:
        """Get ModelAdmin instance for model."""
        return self._registry.get(model)
    
    def get_registered_models(self) -> List[Type[Model]]:
        """Get list of registered models."""
        return list(self._registry.keys())
    
    def authenticate(self, username: str, password: str) -> Optional[AdminUser]:
        """Authenticate admin user."""
        user = self.admin_users.get(username)
        if not user:
            return None
        
        from .auth import PasswordHasher
        if PasswordHasher.verify_password(password, user.password_hash):
            user.last_login = datetime.now()
            return user
        
        return None
    
    def create_admin_user(self, username: str, password: str, email: str = "",
                         is_superuser: bool = False, permissions: List[str] = None):
        """Create a new admin user."""
        from .auth import PasswordHasher
        password_hash = PasswordHasher.hash_password(password)
        
        self.admin_users[username] = AdminUser(
            username=username,
            password_hash=password_hash,
            email=email,
            is_superuser=is_superuser,
            permissions=permissions or []
        )
    
    def get_urls(self) -> List[tuple]:
        """Get URL patterns for admin site."""
        urls = [
            # Main admin views
            ("", self.index_view),
            ("login/", self.login_view),
            ("logout/", self.logout_view),
            
            # Model views
            ("<model_name>/", self.model_list_view),
            ("<model_name>/add/", self.model_add_view),
            ("<model_name>/<object_id>/", self.model_detail_view),
            ("<model_name>/<object_id>/change/", self.model_change_view),
            ("<model_name>/<object_id>/delete/", self.model_delete_view),
            
            # Static files
            ("static/<path:file_path>", self.static_view),
        ]
        return urls
    
    def register_routes(self, app, url_prefix: str = "/admin"):
        """Register admin routes with WolfPy app."""
        # Index
        @app.route(f"{url_prefix}")
        @app.route(f"{url_prefix}/")
        def admin_index(request):
            return self.index_view(request)
        
        # Authentication
        @app.route(f"{url_prefix}/login", methods=['GET', 'POST'])
        def admin_login(request):
            return self.login_view(request)
        
        @app.route(f"{url_prefix}/logout")
        def admin_logout(request):
            return self.logout_view(request)
        
        # Model views
        @app.route(f"{url_prefix}/<model_name>")
        @app.route(f"{url_prefix}/<model_name>/")
        def admin_model_list(request, model_name):
            return self.model_list_view(request, model_name)
        
        @app.route(f"{url_prefix}/<model_name>/add", methods=['GET', 'POST'])
        def admin_model_add(request, model_name):
            return self.model_add_view(request, model_name)
        
        @app.route(f"{url_prefix}/<model_name>/<int:object_id>")
        def admin_model_detail(request, model_name, object_id):
            return self.model_detail_view(request, model_name, object_id)
        
        @app.route(f"{url_prefix}/<model_name>/<int:object_id>/change", methods=['GET', 'POST'])
        def admin_model_change(request, model_name, object_id):
            return self.model_change_view(request, model_name, object_id)
        
        @app.route(f"{url_prefix}/<model_name>/<int:object_id>/delete", methods=['GET', 'POST'])
        def admin_model_delete(request, model_name, object_id):
            return self.model_delete_view(request, model_name, object_id)
        
        # Static files
        @app.route(f"{url_prefix}/static/<path:file_path>")
        def admin_static(request, file_path):
            return self.static_view(request, file_path)


    def index_view(self, request: Request) -> Response:
        """Admin index page."""
        # Check authentication
        if not self._check_auth(request):
            return self._redirect_to_login(request)

        # Get registered models with permissions
        models_info = []
        for model in self.get_registered_models():
            model_admin = self.get_model_admin(model)
            if model_admin.has_view_permission(request):
                model_name = model.__name__.lower()
                models_info.append({
                    'name': model.__name__,
                    'model_name': model_name,
                    'verbose_name': getattr(model, '_verbose_name', model.__name__),
                    'verbose_name_plural': getattr(model, '_verbose_name_plural', f"{model.__name__}s"),
                    'can_add': model_admin.has_add_permission(request),
                    'can_change': model_admin.has_change_permission(request),
                    'can_delete': model_admin.has_delete_permission(request),
                })

        return Response(self._render_template('admin/index.html', {
            'title': self.index_title,
            'site_title': self.site_title,
            'site_header': self.site_header,
            'models': models_info,
            'user': request.admin_user
        }))

    def login_view(self, request: Request) -> Response:
        """Admin login page."""
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')

            if username and password:
                user = self.authenticate(username, password)
                if user:
                    # Set session
                    if hasattr(request, 'session'):
                        request.session['admin_user_id'] = username

                    # Redirect to admin index or next page
                    next_url = request.args.get('next', '/admin/')
                    return Response.redirect(next_url)
                else:
                    error = "Invalid username or password."
            else:
                error = "Please enter both username and password."
        else:
            error = None

        return Response(self._render_template('admin/login.html', {
            'title': 'Log in',
            'site_title': self.site_title,
            'site_header': self.site_header,
            'error': error
        }))

    def logout_view(self, request: Request) -> Response:
        """Admin logout."""
        if hasattr(request, 'session') and 'admin_user_id' in request.session:
            del request.session['admin_user_id']

        return Response.redirect('/admin/login/')

    def model_list_view(self, request: Request, model_name: str) -> Response:
        """Model list view with pagination and filtering."""
        # Check authentication and permissions
        if not self._check_auth(request):
            return self._redirect_to_login(request)

        model = self._get_model_by_name(model_name)
        if not model:
            return Response("Model not found", status=404)

        model_admin = self.get_model_admin(model)
        if not model_admin.has_view_permission(request):
            return Response("Permission denied", status=403)

        # Get queryset
        queryset = model_admin.get_queryset(request)

        # Apply search
        search_query = request.args.get('q', '').strip()
        if search_query and model_admin.get_search_fields():
            # Simple search implementation
            search_conditions = []
            for field_name in model_admin.get_search_fields():
                # This is a simplified search - in production, use proper SQL LIKE
                pass

        # Apply filters
        for filter_field in model_admin.get_list_filter():
            filter_value = request.args.get(filter_field)
            if filter_value:
                # Apply filter (simplified)
                pass

        # Pagination
        page = int(request.args.get('page', 1))
        per_page = model_admin.list_per_page

        # Get objects (simplified - in production, use proper pagination)
        objects = queryset.all()
        total_count = len(objects)

        # Calculate pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_objects = objects[start_idx:end_idx]

        has_previous = page > 1
        has_next = end_idx < total_count

        return Response(self._render_template('admin/change_list.html', {
            'title': f"{model.__name__} list",
            'site_title': self.site_title,
            'site_header': self.site_header,
            'model': model,
            'model_name': model_name,
            'model_admin': model_admin,
            'objects': page_objects,
            'page': page,
            'has_previous': has_previous,
            'has_next': has_next,
            'total_count': total_count,
            'search_query': search_query,
            'user': request.admin_user
        }))

    def model_add_view(self, request: Request, model_name: str) -> Response:
        """Add new model instance."""
        # Check authentication and permissions
        if not self._check_auth(request):
            return self._redirect_to_login(request)

        model = self._get_model_by_name(model_name)
        if not model:
            return Response("Model not found", status=404)

        model_admin = self.get_model_admin(model)
        if not model_admin.has_add_permission(request):
            return Response("Permission denied", status=403)

        if request.method == 'POST':
            # Process form submission
            form_data = {}
            errors = {}

            for field_name, field in model._fields.items():
                if field.primary_key and isinstance(field, IntegerField):
                    continue  # Skip auto-increment primary keys

                value = request.form.get(field_name)
                if value is not None:
                    # Basic type conversion
                    try:
                        if isinstance(field, IntegerField):
                            value = int(value) if value else None
                        elif isinstance(field, BooleanField):
                            value = value.lower() in ('true', '1', 'on', 'yes')
                        elif isinstance(field, DateTimeField):
                            if value:
                                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                            else:
                                value = None

                        form_data[field_name] = value
                    except (ValueError, TypeError) as e:
                        errors[field_name] = [f"Invalid value: {e}"]

            if not errors:
                try:
                    # Create and save instance
                    instance = model(**form_data)
                    validation_errors = instance.validate()

                    if not validation_errors:
                        instance.save()
                        return Response.redirect(f"/admin/{model_name}/")
                    else:
                        errors.update(validation_errors)
                except Exception as e:
                    errors['__all__'] = [f"Error saving: {e}"]
        else:
            form_data = {}
            errors = {}

        return Response(self._render_template('admin/change_form.html', {
            'title': f"Add {model.__name__}",
            'site_title': self.site_title,
            'site_header': self.site_header,
            'model': model,
            'model_name': model_name,
            'model_admin': model_admin,
            'form_data': form_data,
            'errors': errors,
            'is_add': True,
            'user': request.admin_user
        }))

    def _check_auth(self, request: Request) -> bool:
        """Check if user is authenticated."""
        if hasattr(request, 'session') and 'admin_user_id' in request.session:
            user_id = request.session['admin_user_id']
            user = self.admin_users.get(user_id)
            if user:
                request.admin_user = user
                return True
        return False

    def _redirect_to_login(self, request: Request) -> Response:
        """Redirect to login page."""
        login_url = "/admin/login/"
        if request.path != "/admin/" and request.path != "/admin":
            login_url += f"?next={quote(request.path)}"
        return Response.redirect(login_url)

    def _get_model_by_name(self, model_name: str) -> Optional[Type[Model]]:
        """Get model class by name."""
        for model in self.get_registered_models():
            if model.__name__.lower() == model_name.lower():
                return model
        return None

    def model_detail_view(self, request: Request, model_name: str, object_id: int) -> Response:
        """Model detail view (read-only)."""
        return self.model_change_view(request, model_name, object_id, readonly=True)

    def model_change_view(self, request: Request, model_name: str, object_id: int, readonly: bool = False) -> Response:
        """Edit existing model instance."""
        # Check authentication and permissions
        if not self._check_auth(request):
            return self._redirect_to_login(request)

        model = self._get_model_by_name(model_name)
        if not model:
            return Response("Model not found", status=404)

        model_admin = self.get_model_admin(model)
        if readonly:
            if not model_admin.has_view_permission(request):
                return Response("Permission denied", status=403)
        else:
            if not model_admin.has_change_permission(request):
                return Response("Permission denied", status=403)

        # Get object
        try:
            instance = model.objects.get(id=object_id)
        except:
            return Response("Object not found", status=404)

        if request.method == 'POST' and not readonly:
            # Process form submission
            form_data = {}
            errors = {}

            for field_name, field in model._fields.items():
                if field.primary_key:
                    form_data[field_name] = getattr(instance, field_name)
                    continue

                value = request.form.get(field_name)
                if value is not None:
                    # Basic type conversion
                    try:
                        if isinstance(field, IntegerField):
                            value = int(value) if value else None
                        elif isinstance(field, BooleanField):
                            value = value.lower() in ('true', '1', 'on', 'yes')
                        elif isinstance(field, DateTimeField):
                            if value:
                                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                            else:
                                value = None

                        form_data[field_name] = value
                        setattr(instance, field_name, value)
                    except (ValueError, TypeError) as e:
                        errors[field_name] = [f"Invalid value: {e}"]

            if not errors:
                try:
                    validation_errors = instance.validate()

                    if not validation_errors:
                        instance.save()
                        return Response.redirect(f"/admin/{model_name}/")
                    else:
                        errors.update(validation_errors)
                except Exception as e:
                    errors['__all__'] = [f"Error saving: {e}"]
        else:
            # Populate form with current values
            form_data = {}
            for field_name in model._fields.keys():
                form_data[field_name] = getattr(instance, field_name)
            errors = {}

        return Response(self._render_template('admin/change_form.html', {
            'title': f"Change {model.__name__}" if not readonly else f"View {model.__name__}",
            'site_title': self.site_title,
            'site_header': self.site_header,
            'model': model,
            'model_name': model_name,
            'model_admin': model_admin,
            'instance': instance,
            'form_data': form_data,
            'errors': errors,
            'is_add': False,
            'readonly': readonly,
            'user': request.admin_user
        }))

    def model_delete_view(self, request: Request, model_name: str, object_id: int) -> Response:
        """Delete model instance."""
        # Check authentication and permissions
        if not self._check_auth(request):
            return self._redirect_to_login(request)

        model = self._get_model_by_name(model_name)
        if not model:
            return Response("Model not found", status=404)

        model_admin = self.get_model_admin(model)
        if not model_admin.has_delete_permission(request):
            return Response("Permission denied", status=403)

        # Get object
        try:
            instance = model.objects.get(id=object_id)
        except:
            return Response("Object not found", status=404)

        if request.method == 'POST':
            # Confirm deletion
            if request.form.get('confirm') == 'yes':
                try:
                    instance.delete()
                    return Response.redirect(f"/admin/{model_name}/")
                except Exception as e:
                    error = f"Error deleting: {e}"
            else:
                return Response.redirect(f"/admin/{model_name}/")
        else:
            error = None

        return Response(self._render_template('admin/delete_confirmation.html', {
            'title': f"Delete {model.__name__}",
            'site_title': self.site_title,
            'site_header': self.site_header,
            'model': model,
            'model_name': model_name,
            'instance': instance,
            'error': error,
            'user': request.admin_user
        }))

    def static_view(self, request: Request, file_path: str) -> Response:
        """Serve admin static files."""
        # Get admin static directory
        admin_dir = Path(__file__).parent.parent / "admin" / "static"
        file_full_path = admin_dir / file_path

        # Security check
        if not str(file_full_path).startswith(str(admin_dir)):
            return Response("Forbidden", status=403)

        if not file_full_path.exists():
            return Response("Not Found", status=404)

        # Read and serve file
        try:
            with open(file_full_path, 'rb') as f:
                content = f.read()

            # Determine content type
            import mimetypes
            content_type, _ = mimetypes.guess_type(str(file_full_path))
            if not content_type:
                content_type = 'application/octet-stream'

            return Response(content, headers={'Content-Type': content_type})
        except Exception:
            return Response("Internal Server Error", status=500)

    def _render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render admin template."""
        # Get template content
        template_content = self._get_template_content(template_name)

        # Simple template rendering (in production, use proper template engine)
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            if isinstance(value, str):
                template_content = template_content.replace(placeholder, value)
            elif isinstance(value, (int, float)):
                template_content = template_content.replace(placeholder, str(value))
            elif isinstance(value, bool):
                template_content = template_content.replace(placeholder, str(value).lower())
            elif value is None:
                template_content = template_content.replace(placeholder, "")
            elif isinstance(value, list):
                # Handle lists (like models for index page)
                if key == 'models':
                    models_html = ""
                    for model in value:
                        models_html += f"""
                        <tr class="model-{model.get('model_name', '')}">
                            <th scope="row">
                                <a href="/admin/{model.get('model_name', '')}/">{model.get('verbose_name_plural', model.get('name', ''))}</a>
                            </th>
                            <td>
                                {'<a href="/admin/' + model.get('model_name', '') + '/add/" class="addlink">Add</a>' if model.get('can_add') else ''}
                                {'<a href="/admin/' + model.get('model_name', '') + '/" class="changelink">Change</a>' if model.get('can_change') else ''}
                            </td>
                        </tr>"""
                    template_content = template_content.replace("{% for model in models %}", "").replace("{% endfor %}", "").replace(
                        """<tr class="model-{{model.model_name}}">
                                <th scope="row">
                                    <a href="/admin/{{model.model_name}}/">{{model.verbose_name_plural}}</a>
                                </th>
                                <td>
                                    {% if model.can_add %}
                                    <a href="/admin/{{model.model_name}}/add/" class="addlink">Add</a>
                                    {% endif %}
                                    {% if model.can_change %}
                                    <a href="/admin/{{model.model_name}}/" class="changelink">Change</a>
                                    {% endif %}
                                </td>
                            </tr>""", models_html)

        return template_content

    def _get_template_content(self, template_name: str) -> str:
        """Get template content (simplified implementation)."""
        # In production, this would load from actual template files
        # For now, return basic HTML templates

        if template_name == 'admin/index.html':
            return self._get_index_template()
        elif template_name == 'admin/login.html':
            return self._get_login_template()
        elif template_name == 'admin/change_list.html':
            return self._get_change_list_template()
        elif template_name == 'admin/change_form.html':
            return self._get_change_form_template()
        elif template_name == 'admin/delete_confirmation.html':
            return self._get_delete_confirmation_template()
        else:
            return "<html><body><h1>Template not found</h1></body></html>"

    def _get_index_template(self) -> str:
        """Get admin index template."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}} | {{site_title}}</title>
    <link rel="stylesheet" href="/admin/static/admin.css">
</head>
<body class="dashboard">
    <div id="header">
        <div id="branding">
            <h1 id="site-name">{{site_header}}</h1>
        </div>
        <div id="user-tools">
            Welcome, <strong>{{user.username}}</strong> |
            <a href="/admin/logout/">Log out</a>
        </div>
    </div>

    <div class="breadcrumbs">
        <a href="/admin/">Home</a>
    </div>

    <div id="content" class="colM">
        <h1>{{title}}</h1>

        <div id="content-main">
            <div class="app-list">
                <div class="module">
                    <table>
                        <caption>
                            <a href="#" class="section">Models</a>
                        </caption>
                        <tbody>
                            {% for model in models %}
                            <tr class="model-{{model.model_name}}">
                                <th scope="row">
                                    <a href="/admin/{{model.model_name}}/">{{model.verbose_name_plural}}</a>
                                </th>
                                <td>
                                    {% if model.can_add %}
                                    <a href="/admin/{{model.model_name}}/add/" class="addlink">Add</a>
                                    {% endif %}
                                    {% if model.can_change %}
                                    <a href="/admin/{{model.model_name}}/" class="changelink">Change</a>
                                    {% endif %}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""

    def _get_login_template(self) -> str:
        """Get admin login template."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}} | {{site_title}}</title>
    <link rel="stylesheet" href="/admin/static/admin.css">
</head>
<body class="login">
    <div id="container">
        <div id="header">
            <div id="branding">
                <h1 id="site-name">{{site_header}}</h1>
            </div>
        </div>

        <div id="content" class="colM">
            <div id="content-main">
                <form method="post" id="login-form">
                    <div class="form-row">
                        <label for="id_username">Username:</label>
                        <input type="text" name="username" id="id_username" required>
                    </div>
                    <div class="form-row">
                        <label for="id_password">Password:</label>
                        <input type="password" name="password" id="id_password" required>
                    </div>

                    {% if error %}
                    <div class="errornote">{{error}}</div>
                    {% endif %}

                    <div class="submit-row">
                        <input type="submit" value="Log in">
                    </div>
                </form>
            </div>
        </div>
    </div>
</body>
</html>"""

    def _get_change_list_template(self) -> str:
        """Get model list template."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}} | {{site_title}}</title>
    <link rel="stylesheet" href="/admin/static/admin.css">
</head>
<body class="change-list">
    <div id="header">
        <div id="branding">
            <h1 id="site-name">{{site_header}}</h1>
        </div>
        <div id="user-tools">
            Welcome, <strong>{{user.username}}</strong> |
            <a href="/admin/logout/">Log out</a>
        </div>
    </div>

    <div class="breadcrumbs">
        <a href="/admin/">Home</a> &rsaquo; {{model.name}}
    </div>

    <div id="content" class="colM">
        <h1>{{title}}</h1>

        <div id="content-main">
            <div class="module filtered">
                <div id="toolbar">
                    <form id="changelist-search" method="get">
                        <div>
                            <label for="searchbar">Search:</label>
                            <input type="text" size="40" name="q" value="{{search_query}}" id="searchbar">
                            <input type="submit" value="Search">
                        </div>
                    </form>
                </div>

                <div class="results">
                    <table id="result_list">
                        <thead>
                            <tr>
                                {% for field in model_admin.list_display %}
                                <th scope="col">{{field}}</th>
                                {% endfor %}
                                <th scope="col">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for obj in objects %}
                            <tr>
                                {% for field in model_admin.list_display %}
                                <td>{{obj[field]}}</td>
                                {% endfor %}
                                <td>
                                    <a href="/admin/{{model_name}}/{{obj.id}}/">View</a> |
                                    <a href="/admin/{{model_name}}/{{obj.id}}/change/">Edit</a> |
                                    <a href="/admin/{{model_name}}/{{obj.id}}/delete/">Delete</a>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>

                <p class="paginator">
                    {{total_count}} objects
                    {% if has_previous %}
                    <a href="?page={{page|add:-1}}" class="prev">previous</a>
                    {% endif %}
                    Page {{page}}
                    {% if has_next %}
                    <a href="?page={{page|add:1}}" class="next">next</a>
                    {% endif %}
                </p>
            </div>

            <div class="actions">
                <a href="/admin/{{model_name}}/add/" class="addlink">Add {{model.name}}</a>
            </div>
        </div>
    </div>
</body>
</html>"""

    def _get_change_form_template(self) -> str:
        """Get model form template."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}} | {{site_title}}</title>
    <link rel="stylesheet" href="/admin/static/admin.css">
</head>
<body class="change-form">
    <div id="header">
        <div id="branding">
            <h1 id="site-name">{{site_header}}</h1>
        </div>
        <div id="user-tools">
            Welcome, <strong>{{user.username}}</strong> |
            <a href="/admin/logout/">Log out</a>
        </div>
    </div>

    <div class="breadcrumbs">
        <a href="/admin/">Home</a> &rsaquo;
        <a href="/admin/{{model_name}}/">{{model.name}}</a> &rsaquo;
        {% if is_add %}Add{% else %}Change{% endif %}
    </div>

    <div id="content" class="colM">
        <h1>{{title}}</h1>

        <div id="content-main">
            {% if not readonly %}
            <form method="post" id="{{model_name}}_form">
            {% endif %}
                <div>
                    {% if errors.__all__ %}
                    <div class="errornote">{{errors.__all__.0}}</div>
                    {% endif %}

                    <fieldset class="module aligned">
                        {% for field_name, field in model._fields.items %}
                        <div class="form-row">
                            <div>
                                <label for="id_{{field_name}}">{{field_name}}:</label>
                                {% if readonly %}
                                <div class="readonly">{{form_data[field_name]}}</div>
                                {% else %}
                                {% if field.__class__.__name__ == 'BooleanField' %}
                                <input type="checkbox" name="{{field_name}}" id="id_{{field_name}}"
                                       {% if form_data[field_name] %}checked{% endif %}>
                                {% elif field.__class__.__name__ == 'TextField' %}
                                <textarea name="{{field_name}}" id="id_{{field_name}}" rows="10" cols="40">{{form_data[field_name]}}</textarea>
                                {% elif field.__class__.__name__ == 'DateTimeField' %}
                                <input type="datetime-local" name="{{field_name}}" id="id_{{field_name}}"
                                       value="{{form_data[field_name]}}">
                                {% elif field.__class__.__name__ == 'IntegerField' %}
                                <input type="number" name="{{field_name}}" id="id_{{field_name}}"
                                       value="{{form_data[field_name]}}" {% if field.primary_key %}readonly{% endif %}>
                                {% else %}
                                <input type="text" name="{{field_name}}" id="id_{{field_name}}"
                                       value="{{form_data[field_name]}}" {% if field.primary_key %}readonly{% endif %}>
                                {% endif %}
                                {% endif %}

                                {% if errors[field_name] %}
                                <ul class="errorlist">
                                    {% for error in errors[field_name] %}
                                    <li>{{error}}</li>
                                    {% endfor %}
                                </ul>
                                {% endif %}
                            </div>
                        </div>
                        {% endfor %}
                    </fieldset>

                    {% if not readonly %}
                    <div class="submit-row">
                        <input type="submit" value="Save" class="default">
                        <a href="/admin/{{model_name}}/" class="button cancel-link">Cancel</a>
                        {% if not is_add %}
                        <a href="/admin/{{model_name}}/{{instance.id}}/delete/" class="deletelink">Delete</a>
                        {% endif %}
                    </div>
                    {% else %}
                    <div class="submit-row">
                        <a href="/admin/{{model_name}}/" class="button">Back to list</a>
                        <a href="/admin/{{model_name}}/{{instance.id}}/change/" class="button">Edit</a>
                    </div>
                    {% endif %}
                </div>
            {% if not readonly %}
            </form>
            {% endif %}
        </div>
    </div>
</body>
</html>"""

    def _get_delete_confirmation_template(self) -> str:
        """Get delete confirmation template."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}} | {{site_title}}</title>
    <link rel="stylesheet" href="/admin/static/admin.css">
</head>
<body class="delete-confirmation">
    <div id="header">
        <div id="branding">
            <h1 id="site-name">{{site_header}}</h1>
        </div>
        <div id="user-tools">
            Welcome, <strong>{{user.username}}</strong> |
            <a href="/admin/logout/">Log out</a>
        </div>
    </div>

    <div class="breadcrumbs">
        <a href="/admin/">Home</a> &rsaquo;
        <a href="/admin/{{model_name}}/">{{model.name}}</a> &rsaquo;
        Delete
    </div>

    <div id="content" class="colM">
        <h1>{{title}}</h1>

        <div id="content-main">
            {% if error %}
            <div class="errornote">{{error}}</div>
            {% endif %}

            <p>Are you sure you want to delete the {{model.name}} "{{instance}}"? This action cannot be undone.</p>

            <form method="post">
                <div>
                    <input type="hidden" name="confirm" value="yes">
                    <input type="submit" value="Yes, I'm sure" class="default">
                    <a href="/admin/{{model_name}}/" class="button cancel-link">No, take me back</a>
                </div>
            </form>
        </div>
    </div>
</body>
</html>"""


# Global admin site instance
site = AdminSite()


def register(model_or_iterable: Union[Type[Model], List[Type[Model]]],
             admin_class: Type[ModelAdmin] = None):
    """Register model(s) with the default admin site."""
    site.register(model_or_iterable, admin_class)
