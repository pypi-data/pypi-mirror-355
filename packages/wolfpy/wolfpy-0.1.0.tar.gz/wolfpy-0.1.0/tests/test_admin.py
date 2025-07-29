"""
Tests for WolfPy Admin System - Phase 10

This test suite covers the Django-style admin interface functionality:
- Admin site setup and configuration
- Model registration and admin classes
- User authentication and permissions
- CRUD operations through admin interface
- Template rendering and static file serving
"""

import pytest
import tempfile
import os
from unittest.mock import MagicMock, patch

from src.wolfpy import WolfPy
from src.wolfpy.core.database import Database, Model, IntegerField, StringField, BooleanField, DateTimeField
from src.wolfpy.core.admin import AdminSite, ModelAdmin, AdminUser, site as admin_site, register as admin_register
from src.wolfpy.core.request import Request
from src.wolfpy.core.response import Response


class TestModel(Model):
    """Test model for admin testing."""
    id = IntegerField(primary_key=True)
    name = StringField(max_length=100)
    email = StringField(max_length=100)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)


class TestAdminUser:
    """Test AdminUser functionality."""
    
    def test_admin_user_creation(self):
        """Test creating an admin user."""
        user = AdminUser(
            username="testuser",
            password_hash="hashed_password",
            email="test@example.com",
            is_superuser=True,
            permissions=["view_all", "add_all"]
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_superuser is True
        assert "view_all" in user.permissions
        assert user.created_at is not None
    
    def test_admin_user_permissions(self):
        """Test admin user permission checking."""
        # Superuser
        superuser = AdminUser("admin", "hash", is_superuser=True)
        assert superuser.has_permission("any_permission") is True
        assert superuser.can_view_model("testmodel") is True
        assert superuser.can_add_model("testmodel") is True
        assert superuser.can_change_model("testmodel") is True
        assert superuser.can_delete_model("testmodel") is True
        
        # Regular user with specific permissions
        user = AdminUser("user", "hash", permissions=["view_testmodel", "add_testmodel"])
        assert user.has_permission("view_testmodel") is True
        assert user.has_permission("add_testmodel") is True
        assert user.has_permission("delete_testmodel") is False
        assert user.can_view_model("testmodel") is True
        assert user.can_add_model("testmodel") is True
        assert user.can_delete_model("testmodel") is False


class TestModelAdmin:
    """Test ModelAdmin functionality."""
    
    def test_model_admin_creation(self):
        """Test creating a ModelAdmin instance."""
        admin = ModelAdmin(TestModel)
        
        assert admin.model == TestModel
        assert admin.list_per_page == 25
        assert admin.list_display is not None
        assert admin.search_fields is not None
    
    def test_model_admin_auto_configuration(self):
        """Test auto-configuration of ModelAdmin."""
        admin = ModelAdmin(TestModel)
        
        # Should auto-configure list_display with model fields
        assert len(admin.list_display) > 0
        assert 'name' in admin.list_display or 'id' in admin.list_display
        
        # Should auto-configure search fields with string fields
        string_fields = [name for name, field in TestModel._fields.items() 
                        if isinstance(field, StringField)]
        for field in string_fields[:3]:  # Limited to 3 fields
            assert field in admin.search_fields
    
    def test_model_admin_permissions(self):
        """Test ModelAdmin permission checking."""
        admin = ModelAdmin(TestModel)
        
        # Mock request with admin user
        request = MagicMock()
        request.admin_user = AdminUser("admin", "hash", is_superuser=True)
        
        assert admin.has_view_permission(request) is True
        assert admin.has_add_permission(request) is True
        assert admin.has_change_permission(request) is True
        assert admin.has_delete_permission(request) is True
        
        # Mock request without admin user
        request.admin_user = None
        assert admin.has_view_permission(request) is False


class TestAdminSite:
    """Test AdminSite functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.admin_site = AdminSite()
        self.db_file = tempfile.mktemp(suffix='.db')
        self.db = Database(self.db_file)
        self.db.create_tables(TestModel)
    
    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.db_file):
            os.unlink(self.db_file)
    
    def test_admin_site_creation(self):
        """Test creating an AdminSite."""
        site = AdminSite()
        
        assert site.name == "admin"
        assert site.site_title == "WolfPy Administration"
        assert site.site_header == "WolfPy Admin"
        assert len(site.admin_users) > 0  # Default admin user
        assert "admin" in site.admin_users
    
    def test_model_registration(self):
        """Test registering models with admin site."""
        site = AdminSite()
        
        # Register single model
        site.register(TestModel)
        assert site.is_registered(TestModel)
        assert TestModel in site.get_registered_models()
        
        # Register with custom admin class
        class CustomAdmin(ModelAdmin):
            list_display = ['name', 'email']
        
        site.register(TestModel, CustomAdmin)
        admin = site.get_model_admin(TestModel)
        assert isinstance(admin, CustomAdmin)
        assert admin.list_display == ['name', 'email']
    
    def test_admin_user_management(self):
        """Test admin user creation and authentication."""
        site = AdminSite()
        
        # Create admin user
        site.create_admin_user(
            username="testadmin",
            password="testpass",
            email="test@admin.com",
            is_superuser=False,
            permissions=["view_testmodel"]
        )
        
        assert "testadmin" in site.admin_users
        user = site.admin_users["testadmin"]
        assert user.email == "test@admin.com"
        assert user.is_superuser is False
        assert "view_testmodel" in user.permissions
        
        # Test authentication
        authenticated_user = site.authenticate("testadmin", "testpass")
        assert authenticated_user is not None
        assert authenticated_user.username == "testadmin"
        
        # Test failed authentication
        failed_auth = site.authenticate("testadmin", "wrongpass")
        assert failed_auth is None
    
    def test_url_patterns(self):
        """Test admin URL pattern generation."""
        site = AdminSite()
        urls = site.get_urls()
        
        assert len(urls) > 0
        
        # Check for expected URL patterns
        url_patterns = [url[0] for url in urls]
        assert "" in url_patterns  # Index
        assert "login/" in url_patterns
        assert "logout/" in url_patterns
        assert "<model_name>/" in url_patterns
        assert "<model_name>/add/" in url_patterns
    
    @patch('src.wolfpy.core.admin.AdminSite._check_auth')
    def test_index_view(self, mock_check_auth):
        """Test admin index view."""
        site = AdminSite()
        site.register(TestModel)
        
        # Mock authenticated request
        mock_check_auth.return_value = True
        request = MagicMock()
        request.admin_user = AdminUser("admin", "hash", is_superuser=True)
        
        response = site.index_view(request)
        
        assert isinstance(response, Response)
        assert "WolfPy Administration" in response.body
        assert "TestModel" in response.body or "testmodel" in response.body.lower()
    
    @patch('src.wolfpy.core.admin.AdminSite._check_auth')
    def test_login_view_get(self, mock_check_auth):
        """Test admin login view GET request."""
        site = AdminSite()
        
        request = MagicMock()
        request.method = 'GET'
        
        response = site.login_view(request)
        
        assert isinstance(response, Response)
        assert "Log in" in response.body
        assert "username" in response.body.lower()
        assert "password" in response.body.lower()
    
    @patch('src.wolfpy.core.admin.AdminSite._check_auth')
    def test_login_view_post_success(self, mock_check_auth):
        """Test admin login view POST request with valid credentials."""
        site = AdminSite()
        
        request = MagicMock()
        request.method = 'POST'
        request.form = {'username': 'admin', 'password': 'admin123'}
        request.args = {}
        request.session = {}
        
        with patch.object(site, 'authenticate') as mock_auth:
            mock_auth.return_value = AdminUser("admin", "hash", is_superuser=True)
            
            response = site.login_view(request)
            
            assert response.status_code == 302  # Redirect
            assert 'admin_user_id' in request.session
    
    def test_static_file_serving(self):
        """Test admin static file serving."""
        site = AdminSite()
        
        request = MagicMock()
        
        # Test non-existent file
        response = site.static_view(request, "nonexistent.css")
        assert response.status_code == 404
        
        # Test path traversal protection
        response = site.static_view(request, "../../../etc/passwd")
        assert response.status_code == 403


class TestAdminIntegration:
    """Test admin system integration with WolfPy app."""
    
    def setup_method(self):
        """Set up test environment."""
        self.db_file = tempfile.mktemp(suffix='.db')
        self.app = WolfPy(debug=True)
        self.app.db = Database(self.db_file)
        self.app.db.create_tables(TestModel)
    
    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.db_file):
            os.unlink(self.db_file)
    
    def test_admin_route_registration(self):
        """Test registering admin routes with WolfPy app."""
        site = AdminSite()
        site.register(TestModel)
        
        # Register routes
        site.register_routes(self.app)
        
        # Check that routes were registered
        routes = self.app.router.routes
        admin_routes = [route for route in routes if '/admin' in route.pattern]
        
        assert len(admin_routes) > 0
    
    def test_global_admin_register_function(self):
        """Test the global admin_register function."""
        # Clear any existing registrations
        admin_site._registry.clear()
        
        # Register model using global function
        admin_register(TestModel)
        
        assert admin_site.is_registered(TestModel)
        assert TestModel in admin_site.get_registered_models()
        
        # Register with custom admin
        class CustomTestAdmin(ModelAdmin):
            list_display = ['name']
        
        admin_register(TestModel, CustomTestAdmin)
        admin = admin_site.get_model_admin(TestModel)
        assert isinstance(admin, CustomTestAdmin)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
