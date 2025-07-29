"""
WolfPy Authentication Module.

This module provides comprehensive authentication and authorization functionality
including JWT tokens, OAuth2, multi-factor authentication, and advanced security features.
"""

import hashlib
import secrets
import time
import json
import base64
import hmac
import re
from typing import Dict, Any, Optional, Callable, List, Union
from functools import wraps
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False

try:
    import jwt
    HAS_JWT = True
except ImportError:
    HAS_JWT = False

try:
    import pyotp
    HAS_PYOTP = True
except ImportError:
    HAS_PYOTP = False

from .request import Request
from .response import Response


class UserRole(Enum):
    """User role enumeration."""
    GUEST = "guest"
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPERUSER = "superuser"


class AuthProvider(Enum):
    """Authentication provider enumeration."""
    LOCAL = "local"
    GOOGLE = "google"
    GITHUB = "github"
    FACEBOOK = "facebook"
    TWITTER = "twitter"


@dataclass
class UserProfile:
    """Enhanced user profile with additional metadata."""
    id: str
    username: str
    email: str
    first_name: str = ""
    last_name: str = ""
    avatar_url: str = ""
    bio: str = ""
    location: str = ""
    website: str = ""
    phone: str = ""
    date_of_birth: Optional[datetime] = None
    timezone: str = "UTC"
    language: str = "en"
    is_active: bool = True
    is_verified: bool = False
    is_staff: bool = False
    is_superuser: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    login_count: int = 0
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    password_changed_at: Optional[datetime] = None
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
    backup_codes: List[str] = field(default_factory=list)
    roles: List[str] = field(default_factory=lambda: ["user"])
    permissions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    auth_provider: str = AuthProvider.LOCAL.value
    provider_id: Optional[str] = None

    def get_full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}".strip()

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        return permission in self.permissions

    def add_role(self, role: str):
        """Add a role to the user."""
        if role not in self.roles:
            self.roles.append(role)

    def remove_role(self, role: str):
        """Remove a role from the user."""
        if role in self.roles:
            self.roles.remove(role)

    def add_permission(self, permission: str):
        """Add a permission to the user."""
        if permission not in self.permissions:
            self.permissions.append(permission)

    def remove_permission(self, permission: str):
        """Remove a permission from the user."""
        if permission in self.permissions:
            self.permissions.remove(permission)

    def is_locked(self) -> bool:
        """Check if user account is locked."""
        return self.locked_until and datetime.now() < self.locked_until

    def lock_account(self, duration_minutes: int = 30):
        """Lock user account for specified duration."""
        self.locked_until = datetime.now() + timedelta(minutes=duration_minutes)

    def unlock_account(self):
        """Unlock user account."""
        self.locked_until = None
        self.failed_login_attempts = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert user profile to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.get_full_name(),
            'avatar_url': self.avatar_url,
            'bio': self.bio,
            'location': self.location,
            'website': self.website,
            'phone': self.phone,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'timezone': self.timezone,
            'language': self.language,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'is_staff': self.is_staff,
            'is_superuser': self.is_superuser,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'login_count': self.login_count,
            'mfa_enabled': self.mfa_enabled,
            'roles': self.roles,
            'permissions': self.permissions,
            'auth_provider': self.auth_provider,
            'is_locked': self.is_locked(),
            'metadata': self.metadata
        }


class User:
    """
    Legacy User model for backward compatibility.

    Represents a user in the authentication system.
    """

    def __init__(self, user_id: str, username: str, email: str = None, **kwargs):
        """
        Initialize a user.

        Args:
            user_id: Unique user identifier
            username: Username
            email: User email
            **kwargs: Additional user attributes
        """
        self.id = user_id
        self.username = username
        self.email = email
        self.attributes = kwargs

    def get(self, key: str, default: Any = None) -> Any:
        """Get a user attribute."""
        return self.attributes.get(key, default)

    def set(self, key: str, value: Any):
        """Set a user attribute."""
        self.attributes[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            **self.attributes
        }

    def __repr__(self) -> str:
        return f"User(id='{self.id}', username='{self.username}')"


class PasswordPolicy:
    """Password policy enforcement."""

    def __init__(self,
                 min_length: int = 8,
                 require_uppercase: bool = True,
                 require_lowercase: bool = True,
                 require_digits: bool = True,
                 require_special: bool = True,
                 max_length: int = 128,
                 forbidden_passwords: List[str] = None):
        """
        Initialize password policy.

        Args:
            min_length: Minimum password length
            require_uppercase: Require uppercase letters
            require_lowercase: Require lowercase letters
            require_digits: Require digits
            require_special: Require special characters
            max_length: Maximum password length
            forbidden_passwords: List of forbidden passwords
        """
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digits = require_digits
        self.require_special = require_special
        self.max_length = max_length
        self.forbidden_passwords = set(forbidden_passwords or [])

        # Common weak passwords
        self.forbidden_passwords.update([
            'password', '123456', 'password123', 'admin', 'qwerty',
            'letmein', 'welcome', 'monkey', '1234567890', 'abc123'
        ])

    def validate(self, password: str) -> Dict[str, Any]:
        """
        Validate password against policy.

        Args:
            password: Password to validate

        Returns:
            Dictionary with validation results
        """
        errors = []

        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters long")

        if len(password) > self.max_length:
            errors.append(f"Password must be at most {self.max_length} characters long")

        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")

        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")

        if self.require_digits and not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")

        if self.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")

        if password.lower() in self.forbidden_passwords:
            errors.append("Password is too common and not allowed")

        # Calculate password strength
        strength_score = 0
        if len(password) >= 8:
            strength_score += 1
        if len(password) >= 12:
            strength_score += 1
        if re.search(r'[A-Z]', password):
            strength_score += 1
        if re.search(r'[a-z]', password):
            strength_score += 1
        if re.search(r'\d', password):
            strength_score += 1
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            strength_score += 1

        strength_levels = ["Very Weak", "Weak", "Fair", "Good", "Strong", "Very Strong"]
        strength = strength_levels[min(strength_score, len(strength_levels) - 1)]

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'strength': strength,
            'score': strength_score
        }


class PasswordHasher:
    """
    Enhanced password hashing utility.

    Provides secure password hashing and verification with multiple algorithms.
    """

    @staticmethod
    def hash_password(password: str, algorithm: str = 'auto') -> str:
        """
        Hash a password securely.

        Args:
            password: Plain text password
            algorithm: Hashing algorithm ('bcrypt', 'pbkdf2', 'auto')

        Returns:
            Hashed password string
        """
        if algorithm == 'auto':
            algorithm = 'bcrypt' if HAS_BCRYPT else 'pbkdf2'

        if algorithm == 'bcrypt' and HAS_BCRYPT:
            # Use bcrypt if available (recommended)
            salt = bcrypt.gensalt(rounds=12)  # Increased rounds for better security
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return f"bcrypt${hashed.decode('utf-8')}"
        else:
            # Fallback to PBKDF2 with SHA-256
            salt = secrets.token_hex(16)
            hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'),
                                       salt.encode('utf-8'), 100000)
            return f"pbkdf2_sha256${salt}${hashed.hex()}"

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            password: Plain text password
            hashed: Hashed password

        Returns:
            True if password matches, False otherwise
        """
        try:
            if hashed.startswith('bcrypt$') and HAS_BCRYPT:
                # bcrypt hash
                hash_value = hashed[7:]  # Remove 'bcrypt$' prefix
                return bcrypt.checkpw(password.encode('utf-8'), hash_value.encode('utf-8'))
            elif hashed.startswith('pbkdf2_sha256$'):
                # PBKDF2 hash
                parts = hashed.split('$')
                if len(parts) != 3:
                    return False

                salt = parts[1]
                stored_hash = parts[2]

                computed_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'),
                                                  salt.encode('utf-8'), 100000)
                return computed_hash.hex() == stored_hash
            else:
                # Legacy format support
                if HAS_BCRYPT and not hashed.startswith('pbkdf2_'):
                    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
                else:
                    parts = hashed.split('$')
                    if len(parts) == 3 and parts[0] == 'pbkdf2_sha256':
                        salt = parts[1]
                        stored_hash = parts[2]
                        computed_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'),
                                                          salt.encode('utf-8'), 100000)
                        return computed_hash.hex() == stored_hash
                    return False
        except (ValueError, IndexError):
            return False

    @staticmethod
    def needs_rehash(hashed: str) -> bool:
        """
        Check if password hash needs to be updated.

        Args:
            hashed: Hashed password

        Returns:
            True if hash should be updated
        """
        # Recommend rehashing if using old PBKDF2 format or old bcrypt rounds
        if hashed.startswith('pbkdf2_sha256$'):
            return True  # Prefer bcrypt if available
        elif not hashed.startswith('bcrypt$'):
            return True  # Old format
        return False


class JWTManager:
    """
    JWT token management for authentication.

    Handles creation and validation of JWT tokens with refresh token support.
    """

    def __init__(self, secret_key: str, algorithm: str = 'HS256'):
        """
        Initialize JWT manager.

        Args:
            secret_key: Secret key for token signing
            algorithm: JWT algorithm
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.refresh_tokens = {}  # In production, use Redis or database

    def create_access_token(self, user_id: str, expires_in: int = 3600,
                           additional_claims: Dict[str, Any] = None) -> str:
        """
        Create a JWT access token.

        Args:
            user_id: User identifier
            expires_in: Token expiration time in seconds
            additional_claims: Additional claims to include

        Returns:
            JWT access token
        """
        if not HAS_JWT:
            raise RuntimeError("PyJWT is required for JWT token support")

        now = datetime.utcnow()
        payload = {
            'sub': user_id,
            'iat': now,
            'exp': now + timedelta(seconds=expires_in),
            'type': 'access'
        }

        if additional_claims:
            payload.update(additional_claims)

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, user_id: str, expires_in: int = 30 * 24 * 3600) -> str:
        """
        Create a JWT refresh token.

        Args:
            user_id: User identifier
            expires_in: Token expiration time in seconds (default 30 days)

        Returns:
            JWT refresh token
        """
        if not HAS_JWT:
            raise RuntimeError("PyJWT is required for JWT token support")

        now = datetime.utcnow()
        token_id = secrets.token_urlsafe(32)

        payload = {
            'sub': user_id,
            'iat': now,
            'exp': now + timedelta(seconds=expires_in),
            'type': 'refresh',
            'jti': token_id
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

        # Store refresh token (in production, use Redis or database)
        self.refresh_tokens[token_id] = {
            'user_id': user_id,
            'created_at': now,
            'expires_at': now + timedelta(seconds=expires_in)
        }

        return token

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token.

        Args:
            token: JWT token

        Returns:
            Token payload if valid, None otherwise
        """
        if not HAS_JWT:
            return None

        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Check if refresh token is still valid
            if payload.get('type') == 'refresh':
                token_id = payload.get('jti')
                if token_id not in self.refresh_tokens:
                    return None

                token_info = self.refresh_tokens[token_id]
                if datetime.utcnow() > token_info['expires_at']:
                    del self.refresh_tokens[token_id]
                    return None

            return payload

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        Create new access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New access token if refresh token is valid
        """
        payload = self.verify_token(refresh_token)
        if not payload or payload.get('type') != 'refresh':
            return None

        user_id = payload.get('sub')
        return self.create_access_token(user_id)

    def revoke_refresh_token(self, refresh_token: str) -> bool:
        """
        Revoke a refresh token.

        Args:
            refresh_token: Refresh token to revoke

        Returns:
            True if token was revoked
        """
        payload = self.verify_token(refresh_token)
        if not payload or payload.get('type') != 'refresh':
            return False

        token_id = payload.get('jti')
        if token_id in self.refresh_tokens:
            del self.refresh_tokens[token_id]
            return True

        return False


class MFAManager:
    """
    Multi-Factor Authentication manager.

    Handles TOTP (Time-based One-Time Password) and backup codes.
    """

    def __init__(self, issuer_name: str = "WolfPy App"):
        """
        Initialize MFA manager.

        Args:
            issuer_name: Name of the application for TOTP
        """
        self.issuer_name = issuer_name

    def generate_secret(self) -> str:
        """
        Generate a new TOTP secret.

        Returns:
            Base32-encoded secret
        """
        if not HAS_PYOTP:
            raise RuntimeError("pyotp is required for MFA support")

        return pyotp.random_base32()

    def generate_qr_code_url(self, secret: str, user_email: str) -> str:
        """
        Generate QR code URL for TOTP setup.

        Args:
            secret: TOTP secret
            user_email: User's email address

        Returns:
            QR code URL
        """
        if not HAS_PYOTP:
            raise RuntimeError("pyotp is required for MFA support")

        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=user_email,
            issuer_name=self.issuer_name
        )

    def verify_totp(self, secret: str, token: str, window: int = 1) -> bool:
        """
        Verify a TOTP token.

        Args:
            secret: TOTP secret
            token: TOTP token to verify
            window: Time window for verification (default 1 = 30 seconds)

        Returns:
            True if token is valid
        """
        if not HAS_PYOTP:
            return False

        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=window)
        except Exception:
            return False

    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """
        Generate backup codes for MFA.

        Args:
            count: Number of backup codes to generate

        Returns:
            List of backup codes
        """
        codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric codes
            code = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
                          for _ in range(8))
            codes.append(code)
        return codes

    def verify_backup_code(self, user_backup_codes: List[str], code: str) -> bool:
        """
        Verify and consume a backup code.

        Args:
            user_backup_codes: User's backup codes
            code: Backup code to verify

        Returns:
            True if code is valid and was consumed
        """
        code = code.upper().replace(' ', '')
        if code in user_backup_codes:
            user_backup_codes.remove(code)
            return True
        return False


class TokenManager:
    """
    Legacy token management for backward compatibility.

    Handles creation and validation of simple authentication tokens.
    """

    def __init__(self, secret_key: str):
        """
        Initialize token manager.

        Args:
            secret_key: Secret key for token signing
        """
        self.secret_key = secret_key

    def create_token(self, user_id: str, expires_in: int = 3600) -> str:
        """
        Create an authentication token.

        Args:
            user_id: User identifier
            expires_in: Token expiration time in seconds

        Returns:
            Authentication token
        """
        timestamp = int(time.time())
        expiry = timestamp + expires_in

        # Create token payload
        payload = f"{user_id}:{expiry}:{timestamp}"

        # Create signature
        signature = hashlib.sha256(
            f"{payload}:{self.secret_key}".encode('utf-8')
        ).hexdigest()

        return f"{payload}:{signature}"

    def verify_token(self, token: str) -> Optional[str]:
        """
        Verify and extract user ID from token.

        Args:
            token: Authentication token

        Returns:
            User ID if token is valid, None otherwise
        """
        try:
            parts = token.split(':')
            if len(parts) != 4:
                return None

            user_id, expiry_str, timestamp_str, signature = parts

            # Verify signature
            payload = f"{user_id}:{expiry_str}:{timestamp_str}"
            expected_signature = hashlib.sha256(
                f"{payload}:{self.secret_key}".encode('utf-8')
            ).hexdigest()

            if signature != expected_signature:
                return None

            # Check expiration
            expiry = int(expiry_str)
            if time.time() > expiry:
                return None

            return user_id

        except (ValueError, IndexError):
            return None


class Auth:
    """
    Enhanced authentication manager for WolfPy applications.

    Provides comprehensive user authentication, session management, authorization,
    JWT tokens, MFA, and advanced security features.
    """

    def __init__(self, secret_key: str = None, use_jwt: bool = True,
                 enable_mfa: bool = False, password_policy: PasswordPolicy = None):
        """
        Initialize authentication manager.

        Args:
            secret_key: Secret key for token signing
            use_jwt: Whether to use JWT tokens
            enable_mfa: Whether to enable multi-factor authentication
            password_policy: Password policy for validation
        """
        self.secret_key = secret_key or secrets.token_hex(32)
        self.use_jwt = use_jwt and HAS_JWT
        self.enable_mfa = enable_mfa and HAS_PYOTP

        # Initialize managers
        if self.use_jwt:
            self.jwt_manager = JWTManager(self.secret_key)
        self.token_manager = TokenManager(self.secret_key)

        if self.enable_mfa:
            self.mfa_manager = MFAManager()

        self.password_policy = password_policy or PasswordPolicy()

        # User management
        self.user_loader: Optional[Callable] = None
        self.users: Dict[str, Union[User, UserProfile]] = {}  # In-memory user store (for demo)

        # Security settings
        self.max_login_attempts = 5
        self.lockout_duration = 30  # minutes
        self.session_timeout = 3600  # seconds
        self.require_email_verification = False

        # Activity tracking
        self.login_attempts: Dict[str, List[datetime]] = defaultdict(list)
        self.failed_logins: Dict[str, int] = defaultdict(int)
    
    def set_user_loader(self, func: Callable[[str], Optional[Union[User, UserProfile]]]):
        """
        Set a function to load users by ID.

        Args:
            func: Function that takes user_id and returns User/UserProfile or None
        """
        self.user_loader = func

    def load_user(self, user_id: str) -> Optional[Union[User, UserProfile]]:
        """
        Load a user by ID.

        Args:
            user_id: User identifier

        Returns:
            User/UserProfile object or None if not found
        """
        if self.user_loader:
            return self.user_loader(user_id)
        else:
            # Fallback to in-memory store
            return self.users.get(user_id)

    def find_user_by_username(self, username: str) -> Optional[Union[User, UserProfile]]:
        """
        Find a user by username.

        Args:
            username: Username to search for

        Returns:
            User/UserProfile object or None if not found
        """
        for user in self.users.values():
            if user.username == username:
                return user
        return None

    def find_user_by_email(self, email: str) -> Optional[Union[User, UserProfile]]:
        """
        Find a user by email.

        Args:
            email: Email to search for

        Returns:
            User/UserProfile object or None if not found
        """
        for user in self.users.values():
            if hasattr(user, 'email') and user.email == email:
                return user
        return None
    
    def create_user(self, username: str, password: str, email: str = None,
                   use_profile: bool = True, **kwargs) -> Union[User, UserProfile]:
        """
        Create a new user.

        Args:
            username: Username
            password: Plain text password
            email: User email
            use_profile: Whether to create UserProfile (recommended) or legacy User
            **kwargs: Additional user attributes

        Returns:
            Created user object
        """
        # Validate password
        if self.password_policy:
            validation = self.password_policy.validate(password)
            if not validation['valid']:
                raise ValueError(f"Password validation failed: {', '.join(validation['errors'])}")

        # Check if username already exists
        if self.find_user_by_username(username):
            raise ValueError(f"Username '{username}' already exists")

        # Check if email already exists
        if email and self.find_user_by_email(email):
            raise ValueError(f"Email '{email}' already exists")

        user_id = secrets.token_hex(16)
        hashed_password = PasswordHasher.hash_password(password)

        if use_profile:
            # Create enhanced UserProfile
            user = UserProfile(
                id=user_id,
                username=username,
                email=email or "",
                **kwargs
            )
            user.metadata['password_hash'] = hashed_password
            user.password_changed_at = datetime.now()
        else:
            # Create legacy User for backward compatibility
            user = User(user_id, username, email, password_hash=hashed_password, **kwargs)

        # Store in memory (in production, save to database)
        self.users[user_id] = user

        return user

    def create_user_profile(self, username: str, password: str, email: str,
                           **profile_data) -> UserProfile:
        """
        Create a new user with enhanced profile.

        Args:
            username: Username
            password: Plain text password
            email: User email
            **profile_data: Additional profile data

        Returns:
            Created UserProfile object
        """
        return self.create_user(username, password, email, use_profile=True, **profile_data)

    def update_user_profile(self, user_id: str, **updates) -> bool:
        """
        Update user profile data.

        Args:
            user_id: User identifier
            **updates: Fields to update

        Returns:
            True if user was updated
        """
        user = self.load_user(user_id)
        if not user:
            return False

        if isinstance(user, UserProfile):
            for key, value in updates.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            user.updated_at = datetime.now()
        else:
            # Legacy User
            for key, value in updates.items():
                user.set(key, value)

        return True
    
    def authenticate(self, username: str, password: str,
                    request: Request = None) -> Optional[Union[User, UserProfile]]:
        """
        Authenticate a user with username and password.

        Args:
            username: Username or email
            password: Plain text password
            request: HTTP request for security tracking

        Returns:
            User object if authentication successful, None otherwise
        """
        # Find user by username or email
        user = self.find_user_by_username(username) or self.find_user_by_email(username)

        if not user:
            self._log_failed_login(username, request)
            return None

        # Check if account is locked
        if isinstance(user, UserProfile) and user.is_locked():
            self._log_failed_login(username, request, "account_locked")
            return None

        # Check failed login attempts for legacy users
        if not isinstance(user, UserProfile):
            failed_attempts = self.failed_logins.get(user.id, 0)
            if failed_attempts >= self.max_login_attempts:
                self._log_failed_login(username, request, "too_many_attempts")
                return None

        # Get password hash
        if isinstance(user, UserProfile):
            password_hash = user.metadata.get('password_hash')
        else:
            password_hash = user.get('password_hash')

        if not password_hash:
            self._log_failed_login(username, request, "no_password")
            return None

        # Verify password
        if PasswordHasher.verify_password(password, password_hash):
            # Successful authentication
            self._log_successful_login(user, request)

            # Check if password needs rehashing
            if PasswordHasher.needs_rehash(password_hash):
                new_hash = PasswordHasher.hash_password(password)
                if isinstance(user, UserProfile):
                    user.metadata['password_hash'] = new_hash
                else:
                    user.set('password_hash', new_hash)

            return user
        else:
            # Failed authentication
            self._log_failed_login(username, request, "invalid_password")
            return None

    def _log_successful_login(self, user: Union[User, UserProfile], request: Request = None):
        """Log successful login attempt."""
        if isinstance(user, UserProfile):
            user.last_login = datetime.now()
            user.login_count += 1
            user.failed_login_attempts = 0
            user.unlock_account()
        else:
            # Reset failed attempts for legacy users
            self.failed_logins[user.id] = 0

        # Clear login attempts tracking
        if user.username in self.login_attempts:
            del self.login_attempts[user.username]

    def _log_failed_login(self, username: str, request: Request = None, reason: str = "invalid_credentials"):
        """Log failed login attempt."""
        now = datetime.now()

        # Track login attempts
        self.login_attempts[username].append(now)

        # Clean old attempts (older than 1 hour)
        cutoff = now - timedelta(hours=1)
        self.login_attempts[username] = [
            attempt for attempt in self.login_attempts[username]
            if attempt > cutoff
        ]

        # Find user to update failed attempts
        user = self.find_user_by_username(username) or self.find_user_by_email(username)
        if user:
            if isinstance(user, UserProfile):
                user.failed_login_attempts += 1

                # Lock account if too many failed attempts
                if user.failed_login_attempts >= self.max_login_attempts:
                    user.lock_account(self.lockout_duration)
            else:
                # Track failed attempts for legacy users
                self.failed_logins[user.id] += 1

        # Log security event (in production, log to security system)
        if request:
            ip_address = getattr(request, 'remote_addr', 'unknown')
            user_agent = request.headers.get('User-Agent', 'unknown')
            print(f"Failed login attempt: {username} from {ip_address} ({reason})")

    def is_rate_limited(self, username: str, max_attempts: int = 10, window_minutes: int = 15) -> bool:
        """
        Check if user is rate limited for login attempts.

        Args:
            username: Username to check
            max_attempts: Maximum attempts allowed
            window_minutes: Time window in minutes

        Returns:
            True if rate limited
        """
        if username not in self.login_attempts:
            return False

        cutoff = datetime.now() - timedelta(minutes=window_minutes)
        recent_attempts = [
            attempt for attempt in self.login_attempts[username]
            if attempt > cutoff
        ]

        return len(recent_attempts) >= max_attempts
    
    def login_user(self, user: Union[User, UserProfile], remember: bool = False) -> Dict[str, str]:
        """
        Log in a user and create authentication tokens.

        Args:
            user: User to log in
            remember: Whether to create a long-lived token

        Returns:
            Dictionary with access_token and optionally refresh_token
        """
        expires_in = 30 * 24 * 3600 if remember else 3600  # 30 days or 1 hour

        if self.use_jwt:
            # Create JWT tokens
            access_token = self.jwt_manager.create_access_token(user.id, expires_in)
            result = {'access_token': access_token, 'token_type': 'Bearer'}

            if remember:
                refresh_token = self.jwt_manager.create_refresh_token(user.id)
                result['refresh_token'] = refresh_token

            return result
        else:
            # Create simple token
            token = self.token_manager.create_token(user.id, expires_in)
            return {'access_token': token, 'token_type': 'Bearer'}

    def refresh_token(self, refresh_token: str) -> Optional[str]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New access token if successful
        """
        if not self.use_jwt:
            return None

        return self.jwt_manager.refresh_access_token(refresh_token)

    def revoke_token(self, refresh_token: str) -> bool:
        """
        Revoke a refresh token.

        Args:
            refresh_token: Refresh token to revoke

        Returns:
            True if token was revoked
        """
        if not self.use_jwt:
            return False

        return self.jwt_manager.revoke_refresh_token(refresh_token)

    def setup_mfa(self, user_id: str) -> Dict[str, Any]:
        """
        Set up multi-factor authentication for a user.

        Args:
            user_id: User identifier

        Returns:
            Dictionary with secret and QR code URL
        """
        if not self.enable_mfa:
            raise RuntimeError("MFA is not enabled")

        user = self.load_user(user_id)
        if not user:
            raise ValueError("User not found")

        if not isinstance(user, UserProfile):
            raise ValueError("MFA requires UserProfile")

        # Generate secret
        secret = self.mfa_manager.generate_secret()
        qr_url = self.mfa_manager.generate_qr_code_url(secret, user.email)

        # Generate backup codes
        backup_codes = self.mfa_manager.generate_backup_codes()

        # Store in user profile (don't enable until verified)
        user.mfa_secret = secret
        user.backup_codes = backup_codes

        return {
            'secret': secret,
            'qr_code_url': qr_url,
            'backup_codes': backup_codes
        }

    def verify_mfa_setup(self, user_id: str, token: str) -> bool:
        """
        Verify MFA setup with TOTP token.

        Args:
            user_id: User identifier
            token: TOTP token

        Returns:
            True if setup is verified
        """
        if not self.enable_mfa:
            return False

        user = self.load_user(user_id)
        if not user or not isinstance(user, UserProfile):
            return False

        if not user.mfa_secret:
            return False

        # Verify token
        if self.mfa_manager.verify_totp(user.mfa_secret, token):
            user.mfa_enabled = True
            return True

        return False

    def verify_mfa_token(self, user_id: str, token: str) -> bool:
        """
        Verify MFA token for authentication.

        Args:
            user_id: User identifier
            token: TOTP token or backup code

        Returns:
            True if token is valid
        """
        if not self.enable_mfa:
            return True  # MFA disabled, always pass

        user = self.load_user(user_id)
        if not user or not isinstance(user, UserProfile):
            return False

        if not user.mfa_enabled:
            return True  # MFA not enabled for user

        # Try TOTP first
        if user.mfa_secret and self.mfa_manager.verify_totp(user.mfa_secret, token):
            return True

        # Try backup code
        if self.mfa_manager.verify_backup_code(user.backup_codes, token):
            return True

        return False

    def disable_mfa(self, user_id: str) -> bool:
        """
        Disable MFA for a user.

        Args:
            user_id: User identifier

        Returns:
            True if MFA was disabled
        """
        user = self.load_user(user_id)
        if not user or not isinstance(user, UserProfile):
            return False

        user.mfa_enabled = False
        user.mfa_secret = None
        user.backup_codes = []

        return True
    
    def get_current_user(self, request: Request) -> Optional[Union[User, UserProfile]]:
        """
        Get the current authenticated user from request.

        Args:
            request: HTTP request

        Returns:
            Current user or None if not authenticated
        """
        # First try to get user from session
        if hasattr(request, 'session') and request.session:
            user_id = request.session.get('user_id')
            if user_id:
                user = self.load_user(user_id)
                if user:
                    return user

        # Try to get token from Authorization header
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
        else:
            # Try to get token from cookie
            token = request.get_cookie('auth_token')

        if not token:
            return None

        # Verify token and get user ID
        user_id = None

        if self.use_jwt:
            # Try JWT first
            payload = self.jwt_manager.verify_token(token)
            if payload and payload.get('type') == 'access':
                user_id = payload.get('sub')

        if not user_id:
            # Fallback to simple token
            user_id = self.token_manager.verify_token(token)

        if not user_id:
            return None

        # Load and return user
        return self.load_user(user_id)

    def login_user_session(self, user: Union[User, UserProfile], request: Request, remember: bool = False):
        """
        Log in a user using session-based authentication.

        Args:
            user: User to log in
            request: HTTP request (must have session)
            remember: Whether to extend session lifetime
        """
        if hasattr(request, 'session') and request.session:
            request.session['user_id'] = user.id
            request.session['username'] = user.username
            request.session['login_time'] = time.time()

            if remember:
                # Extend session lifetime for "remember me"
                request.session['remember'] = True

            # Store additional user info for UserProfile
            if isinstance(user, UserProfile):
                request.session['user_email'] = user.email
                request.session['user_roles'] = user.roles
                request.session['mfa_verified'] = not user.mfa_enabled  # Will be updated after MFA

    def logout_user_session(self, request: Request):
        """
        Log out a user from session-based authentication.

        Args:
            request: HTTP request (must have session)
        """
        if hasattr(request, 'session') and request.session:
            request.session.clear()

    def is_user_authenticated(self, request: Request) -> bool:
        """
        Check if user is authenticated.

        Args:
            request: HTTP request

        Returns:
            True if user is authenticated, False otherwise
        """
        return self.get_current_user(request) is not None

    def require_mfa_verification(self, request: Request) -> bool:
        """
        Check if current user requires MFA verification.

        Args:
            request: HTTP request

        Returns:
            True if MFA verification is required
        """
        user = self.get_current_user(request)
        if not user or not isinstance(user, UserProfile):
            return False

        if not user.mfa_enabled:
            return False

        # Check session for MFA verification
        if hasattr(request, 'session') and request.session:
            return not request.session.get('mfa_verified', False)

        return True

    def mark_mfa_verified(self, request: Request):
        """
        Mark MFA as verified in session.

        Args:
            request: HTTP request
        """
        if hasattr(request, 'session') and request.session:
            request.session['mfa_verified'] = True

    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """
        Change user password.

        Args:
            user_id: User identifier
            old_password: Current password
            new_password: New password

        Returns:
            True if password was changed
        """
        user = self.load_user(user_id)
        if not user:
            return False

        # Verify old password
        if isinstance(user, UserProfile):
            old_hash = user.metadata.get('password_hash')
        else:
            old_hash = user.get('password_hash')

        if not old_hash or not PasswordHasher.verify_password(old_password, old_hash):
            return False

        # Validate new password
        if self.password_policy:
            validation = self.password_policy.validate(new_password)
            if not validation['valid']:
                raise ValueError(f"Password validation failed: {', '.join(validation['errors'])}")

        # Hash and store new password
        new_hash = PasswordHasher.hash_password(new_password)

        if isinstance(user, UserProfile):
            user.metadata['password_hash'] = new_hash
            user.password_changed_at = datetime.now()
        else:
            user.set('password_hash', new_hash)

        return True


def login_required(auth: Auth = None, redirect_url: str = '/login', require_mfa: bool = True):
    """
    Decorator to require authentication for a route.

    Args:
        auth: Auth instance (optional if request has auth)
        redirect_url: URL to redirect to if not authenticated
        require_mfa: Whether to require MFA verification if enabled

    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(request: Request, *args, **kwargs):
            # Use provided auth or try to get from request context
            auth_manager = auth
            if not auth_manager and hasattr(request, '_app'):
                auth_manager = getattr(request._app, 'auth', None)

            if not auth_manager:
                return Response.server_error("Authentication system not configured")

            user = auth_manager.get_current_user(request)
            if not user:
                # Check if this is an API request (JSON or has Authorization header)
                is_api_request = (
                    request.headers.get('Content-Type', '').startswith('application/json') or
                    'Authorization' in request.headers or
                    request.headers.get('Accept', '').startswith('application/json')
                )

                if is_api_request:
                    return Response.unauthorized("Authentication required")
                else:
                    # Redirect to login page for web requests
                    return Response.redirect(redirect_url)

            # Check MFA requirement
            if require_mfa and auth_manager.require_mfa_verification(request):
                is_api_request = (
                    request.headers.get('Content-Type', '').startswith('application/json') or
                    'Authorization' in request.headers or
                    request.headers.get('Accept', '').startswith('application/json')
                )

                if is_api_request:
                    return Response.unauthorized("MFA verification required")
                else:
                    return Response.redirect('/mfa/verify')

            # Add user to request for convenience
            request.user = user
            return func(request, *args, **kwargs)

        return wrapper
    return decorator


def permission_required(permission: str, auth: Auth = None):
    """
    Decorator to require a specific permission for a route.

    Args:
        permission: Required permission
        auth: Auth instance (optional if request has auth)

    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(request: Request, *args, **kwargs):
            # Use provided auth or try to get from request context
            auth_manager = auth
            if not auth_manager and hasattr(request, '_app'):
                auth_manager = getattr(request._app, 'auth', None)

            if not auth_manager:
                return Response.server_error("Authentication system not configured")

            user = auth_manager.get_current_user(request)
            if not user:
                return Response.unauthorized("Authentication required")

            # Check permission
            has_permission = False
            if isinstance(user, UserProfile):
                has_permission = user.has_permission(permission)
            else:
                # Legacy User
                user_permissions = user.get('permissions', [])
                has_permission = permission in user_permissions

            if not has_permission:
                return Response.forbidden("Insufficient permissions")

            request.user = user
            return func(request, *args, **kwargs)

        return wrapper
    return decorator


def role_required(role: str, auth: Auth = None):
    """
    Decorator to require a specific role for a route.

    Args:
        role: Required role
        auth: Auth instance (optional if request has auth)

    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(request: Request, *args, **kwargs):
            # Use provided auth or try to get from request context
            auth_manager = auth
            if not auth_manager and hasattr(request, '_app'):
                auth_manager = getattr(request._app, 'auth', None)

            if not auth_manager:
                return Response.server_error("Authentication system not configured")

            user = auth_manager.get_current_user(request)
            if not user:
                return Response.unauthorized("Authentication required")

            # Check role
            has_role = False
            if isinstance(user, UserProfile):
                has_role = user.has_role(role)
            else:
                # Legacy User
                user_roles = user.get('roles', [])
                has_role = role in user_roles

            if not has_role:
                return Response.forbidden(f"Role '{role}' required")

            request.user = user
            return func(request, *args, **kwargs)

        return wrapper
    return decorator


def mfa_required(auth: Auth = None):
    """
    Decorator to require MFA verification for a route.

    Args:
        auth: Auth instance (optional if request has auth)

    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(request: Request, *args, **kwargs):
            # Use provided auth or try to get from request context
            auth_manager = auth
            if not auth_manager and hasattr(request, '_app'):
                auth_manager = getattr(request._app, 'auth', None)

            if not auth_manager:
                return Response.server_error("Authentication system not configured")

            user = auth_manager.get_current_user(request)
            if not user:
                return Response.unauthorized("Authentication required")

            # Check MFA requirement
            if auth_manager.require_mfa_verification(request):
                is_api_request = (
                    request.headers.get('Content-Type', '').startswith('application/json') or
                    'Authorization' in request.headers or
                    request.headers.get('Accept', '').startswith('application/json')
                )

                if is_api_request:
                    return Response.unauthorized("MFA verification required")
                else:
                    return Response.redirect('/mfa/verify')

            request.user = user
            return func(request, *args, **kwargs)

        return wrapper
    return decorator


def anonymous_required(redirect_url: str = '/dashboard'):
    """
    Decorator to require that user is NOT authenticated (for login/register pages).

    Args:
        redirect_url: URL to redirect to if user is authenticated

    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(request: Request, *args, **kwargs):
            # Try to get auth from request context
            auth_manager = None
            if hasattr(request, '_app'):
                auth_manager = getattr(request._app, 'auth', None)

            if auth_manager:
                user = auth_manager.get_current_user(request)
                if user:
                    # User is already authenticated, redirect
                    return Response.redirect(redirect_url)

            return func(request, *args, **kwargs)

        return wrapper
    return decorator
