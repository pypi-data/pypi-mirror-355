"""
Tests for WolfPy Authentication System.

This test suite covers the core authentication functionality including:
- User management
- Password hashing and validation
- JWT token authentication
- Multi-factor authentication
- Session management
- Role-based access control
"""

import os
import tempfile
import pytest
import time
from unittest.mock import patch, MagicMock

from src.wolfpy import WolfPy
from src.wolfpy.core.auth import (
    Auth, User, UserProfile, PasswordHasher, PasswordPolicy,
    JWTManager, MFAManager, TokenManager,
    login_required, permission_required, role_required, mfa_required
)
from src.wolfpy.core.request import Request
from src.wolfpy.core.response import Response


class TestUserManagement:
    """Test user creation and management."""
    
    def setup_method(self):
        """Set up test environment."""
        self.auth = Auth(secret_key="test-secret-key")
    
    def test_create_user(self):
        """Test basic user creation."""
        user = self.auth.create_user(
            username="testuser",
            password="Password123!",
            email="test@example.com"
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.id is not None
        
        # Test user retrieval
        retrieved_user = self.auth.load_user(user.id)
        assert retrieved_user is not None
        assert retrieved_user.username == "testuser"
    
    def test_create_user_profile(self):
        """Test enhanced user profile creation."""
        user = self.auth.create_user_profile(
            username="profileuser",
            password="Password123!",
            email="profile@example.com",
            first_name="Test",
            last_name="User"
        )
        
        assert isinstance(user, UserProfile)
        assert user.username == "profileuser"
        assert user.email == "profile@example.com"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.get_full_name() == "Test User"
        assert "user" in user.roles  # Default role
    
    def test_find_user_methods(self):
        """Test methods to find users."""
        self.auth.create_user(
            username="findme",
            password="Password123!",
            email="find@example.com"
        )
        
        user1 = self.auth.find_user_by_username("findme")
        assert user1 is not None
        assert user1.username == "findme"
        
        user2 = self.auth.find_user_by_email("find@example.com")
        assert user2 is not None
        assert user2.email == "find@example.com"
        
        # Test non-existent user
        assert self.auth.find_user_by_username("nonexistent") is None
        assert self.auth.find_user_by_email("nonexistent@example.com") is None


class TestPasswordSecurity:
    """Test password hashing and validation."""
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "SecurePassword123!"
        hashed = PasswordHasher.hash_password(password)
        
        assert hashed is not None
        assert hashed != password  # Ensure it's actually hashed
        
        # Verify correct password
        assert PasswordHasher.verify_password(password, hashed)
        
        # Verify incorrect password
        assert not PasswordHasher.verify_password("WrongPassword", hashed)
    
    def test_password_policy(self):
        """Test password policy validation."""
        policy = PasswordPolicy(
            min_length=8,
            require_uppercase=True,
            require_lowercase=True,
            require_digits=True,
            require_special=True
        )
        
        # Test valid password
        result = policy.validate("StrongP@ssw0rd")
        assert result["valid"]
        assert result["score"] >= 5
        
        # Test too short
        result = policy.validate("Short1!")
        assert not result["valid"]
        assert any("characters" in err for err in result["errors"])
        
        # Test missing uppercase
        result = policy.validate("lowercase123!")
        assert not result["valid"]
        assert any("uppercase" in err for err in result["errors"])
        
        # Test missing digit
        result = policy.validate("NoDigits!")
        assert not result["valid"]
        assert any("digit" in err for err in result["errors"])
        
        # Test missing special char
        result = policy.validate("NoSpecialChar123")
        assert not result["valid"]
        assert any("special" in err for err in result["errors"])


class TestAuthentication:
    """Test user authentication."""
    
    def setup_method(self):
        """Set up test environment."""
        self.auth = Auth(secret_key="test-secret-key")
        
        # Create test users
        self.user = self.auth.create_user(
            username="authuser",
            password="Password123!",
            email="auth@example.com"
        )
        
        self.profile_user = self.auth.create_user_profile(
            username="profileauth",
            password="Password123!",
            email="profileauth@example.com"
        )
    
    def test_basic_authentication(self):
        """Test basic username/password authentication."""
        # Successful authentication
        authenticated_user = self.auth.authenticate("authuser", "Password123!")
        assert authenticated_user is not None
        assert authenticated_user.id == self.user.id
        
        # Failed authentication - wrong password
        assert self.auth.authenticate("authuser", "WrongPassword") is None
        
        # Failed authentication - wrong username
        assert self.auth.authenticate("wronguser", "Password123!") is None
    
    def test_authentication_with_email(self):
        """Test authentication with email instead of username."""
        authenticated_user = self.auth.authenticate("auth@example.com", "Password123!")
        assert authenticated_user is not None
        assert authenticated_user.id == self.user.id
    
    def test_login_token_generation(self):
        """Test login token generation."""
        token_data = self.auth.login_user(self.user)
        
        assert "access_token" in token_data
        assert token_data["token_type"] == "Bearer"
        
        # Test with remember=True
        token_data_remember = self.auth.login_user(self.user, remember=True)
        assert "access_token" in token_data_remember
        
        if self.auth.use_jwt:
            assert "refresh_token" in token_data_remember


class TestJWTAuthentication:
    """Test JWT authentication if available."""
    
    def setup_method(self):
        """Set up test environment."""
        try:
            import jwt
            self.jwt_available = True
        except ImportError:
            self.jwt_available = False
            pytest.skip("PyJWT not installed, skipping JWT tests")
            
        self.auth = Auth(
            secret_key="jwt-test-secret",
            use_jwt=True
        )
        
        self.user = self.auth.create_user(
            username="jwtuser",
            password="Password123!",
            email="jwt@example.com"
        )
    
    def test_jwt_token_creation(self):
        """Test JWT token creation and validation."""
        if not self.jwt_available:
            return
            
        jwt_manager = JWTManager("jwt-test-secret")
        
        # Create access token
        access_token = jwt_manager.create_access_token(
            user_id=self.user.id,
            expires_in=3600
        )
        
        assert access_token is not None
        
        # Verify token
        payload = jwt_manager.verify_token(access_token)
        assert payload is not None
        assert payload["sub"] == self.user.id
        assert payload["type"] == "access"
        
        # Create refresh token
        refresh_token = jwt_manager.create_refresh_token(
            user_id=self.user.id
        )
        
        assert refresh_token is not None
        
        # Verify refresh token
        payload = jwt_manager.verify_token(refresh_token)
        assert payload is not None
        assert payload["sub"] == self.user.id
        assert payload["type"] == "refresh"
    
    def test_token_refresh(self):
        """Test refreshing access token with refresh token."""
        if not self.jwt_available:
            return
            
        # Login to get tokens
        tokens = self.auth.login_user(self.user, remember=True)
        
        if "refresh_token" not in tokens:
            pytest.skip("JWT refresh tokens not enabled")
            
        # Refresh token
        new_access_token = self.auth.refresh_token(tokens["refresh_token"])
        assert new_access_token is not None
        
        # Verify new token
        payload = self.auth.jwt_manager.verify_token(new_access_token)
        assert payload is not None
        assert payload["sub"] == self.user.id


class TestMFASupport:
    """Test multi-factor authentication if available."""
    
    def setup_method(self):
        """Set up test environment."""
        try:
            import pyotp
            self.mfa_available = True
        except ImportError:
            self.mfa_available = False
            pytest.skip("pyotp not installed, skipping MFA tests")
            
        self.auth = Auth(
            secret_key="mfa-test-secret",
            enable_mfa=True
        )
        
        self.user = self.auth.create_user_profile(
            username="mfauser",
            password="Password123!",
            email="mfa@example.com"
        )
    
    def test_mfa_setup(self):
        """Test MFA setup."""
        if not self.mfa_available:
            return
            
        # Setup MFA
        mfa_data = self.auth.setup_mfa(self.user.id)
        
        assert "secret" in mfa_data
        assert "qr_code_url" in mfa_data
        assert "backup_codes" in mfa_data
        assert len(mfa_data["backup_codes"]) > 0
        
        # Verify MFA setup with mock
        with patch.object(self.auth.mfa_manager, "verify_totp", return_value=True):
            result = self.auth.verify_mfa_setup(self.user.id, "123456")
            assert result is True
            
            # Check that MFA is now enabled
            user = self.auth.load_user(self.user.id)
            assert user.mfa_enabled is True
    
    def test_backup_codes(self):
        """Test MFA backup codes."""
        if not self.mfa_available:
            return
            
        mfa_manager = MFAManager()
        
        # Generate backup codes
        codes = mfa_manager.generate_backup_codes(count=10)
        assert len(codes) == 10
        
        # Test backup code verification
        backup_codes = codes.copy()
        assert mfa_manager.verify_backup_code(backup_codes, codes[0])
        
        # Code should be consumed
        assert len(backup_codes) == 9
        assert codes[0] not in backup_codes


class TestRolePermissions:
    """Test role and permission management."""
    
    def setup_method(self):
        """Set up test environment."""
        self.auth = Auth(secret_key="role-test-secret")
        
        self.user = self.auth.create_user_profile(
            username="roleuser",
            password="Password123!",
            email="role@example.com"
        )
    
    def test_role_management(self):
        """Test adding and removing roles."""
        # Default role
        assert self.user.has_role("user")
        
        # Add role
        self.user.add_role("admin")
        assert self.user.has_role("admin")
        
        # Remove role
        self.user.remove_role("admin")
        assert not self.user.has_role("admin")
        
        # Add multiple roles
        self.user.add_role("editor")
        self.user.add_role("moderator")
        assert self.user.has_role("editor")
        assert self.user.has_role("moderator")
    
    def test_permission_management(self):
        """Test adding and removing permissions."""
        # Add permissions
        self.user.add_permission("read")
        self.user.add_permission("write")
        
        assert self.user.has_permission("read")
        assert self.user.has_permission("write")
        assert not self.user.has_permission("delete")
        
        # Remove permission
        self.user.remove_permission("write")
        assert not self.user.has_permission("write")


class TestAuthDecorators:
    """Test authentication decorators."""
    
    def setup_method(self):
        """Set up test environment."""
        self.auth = Auth(secret_key="decorator-test-secret")
        
        # Create test user with roles and permissions
        self.user = self.auth.create_user_profile(
            username="decoratoruser",
            password="Password123!",
            email="decorator@example.com"
        )
        self.user.add_role("admin")
        self.user.add_permission("read")
        
        # Mock request
        self.request = MagicMock()
        self.request._app = MagicMock()
        self.request._app.auth = self.auth
        self.request.headers = {}
    
    def test_login_required_decorator(self):
        """Test login_required decorator."""
        # Create test route
        @login_required()
        def protected_route(request):
            return "Protected content"
        
        # Test with authenticated user
        with patch.object(self.auth, "get_current_user", return_value=self.user):
            result = protected_route(self.request)
            assert result == "Protected content"
            assert hasattr(self.request, "user")
            assert self.request.user == self.user
        
        # Test with unauthenticated user
        with patch.object(self.auth, "get_current_user", return_value=None):
            result = protected_route(self.request)
            assert isinstance(result, Response)
            assert result.status_code in (401, 302)  # Either unauthorized or redirect
    
    def test_role_required_decorator(self):
        """Test role_required decorator."""
        # Create test route
        @role_required("admin")
        def admin_route(request):
            return "Admin content"
        
        # Test with admin user
        with patch.object(self.auth, "get_current_user", return_value=self.user):
            result = admin_route(self.request)
            assert result == "Admin content"
        
        # Test with non-admin user
        self.user.remove_role("admin")
        with patch.object(self.auth, "get_current_user", return_value=self.user):
            result = admin_route(self.request)
            assert isinstance(result, Response)
            assert result.status_code == 403  # Forbidden
    
    def test_permission_required_decorator(self):
        """Test permission_required decorator."""
        # Create test route
        @permission_required("read")
        def read_route(request):
            return "Readable content"
        
        # Test with user having read permission
        with patch.object(self.auth, "get_current_user", return_value=self.user):
            result = read_route(self.request)
            assert result == "Readable content"
        
        # Test with user lacking read permission
        self.user.remove_permission("read")
        with patch.object(self.auth, "get_current_user", return_value=self.user):
            result = read_route(self.request)
            assert isinstance(result, Response)
            assert result.status_code == 403  # Forbidden


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
