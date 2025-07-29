"""
WolfPy Session Module.

This module provides enhanced session management functionality for maintaining
user state across HTTP requests with improved security, performance monitoring,
and multiple storage backends including memory, file, SQLite, and Redis.
"""

import json
import time
import secrets
import hashlib
import threading
import sqlite3
import hmac
import base64
import ipaddress
from typing import Dict, Any, Optional, Union, List, Set, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from .request import Request
from .response import Response


class SessionStore:
    """
    Base class for session storage backends.
    """
    
    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data by ID."""
        raise NotImplementedError
    
    def set(self, session_id: str, data: Dict[str, Any], expires: int = None):
        """Set session data."""
        raise NotImplementedError
    
    def delete(self, session_id: str):
        """Delete session data."""
        raise NotImplementedError
    
    def cleanup(self):
        """Clean up expired sessions."""
        raise NotImplementedError


class MemorySessionStore(SessionStore):
    """
    In-memory session storage.
    
    Note: This is not suitable for production use with multiple processes
    or when persistence across restarts is required.
    """
    
    def __init__(self, max_sessions: int = 10000, cleanup_interval: int = 300):
        """
        Initialize enhanced memory session store.

        Args:
            max_sessions: Maximum number of sessions to store in memory
            cleanup_interval: Interval in seconds for cleaning up expired sessions
        """
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.max_sessions = max_sessions
        self.cleanup_interval = cleanup_interval
        self._last_cleanup = time.time()

        # Performance monitoring
        self._stats = {
            'total_sessions_created': 0,
            'total_sessions_expired': 0,
            'total_sessions_deleted': 0,
            'cleanup_runs': 0,
            'current_sessions': 0
        }
    
    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data by ID."""
        session_data = self.sessions.get(session_id)
        if not session_data:
            return None
        
        # Check expiration
        if session_data.get('_expires', 0) < time.time():
            self.delete(session_id)
            return None
        
        return session_data.get('data', {})
    
    def set(self, session_id: str, data: Dict[str, Any], expires: int = None):
        """Set session data with automatic cleanup and limits."""
        if expires is None:
            expires = int(time.time()) + 3600  # 1 hour default

        # Check if this is a new session
        is_new_session = session_id not in self.sessions

        # Enforce session limit
        if is_new_session and len(self.sessions) >= self.max_sessions:
            self._cleanup_oldest_sessions()

        self.sessions[session_id] = {
            'data': data,
            '_expires': expires,
            '_created': time.time(),
            '_last_accessed': time.time()
        }

        if is_new_session:
            self._stats['total_sessions_created'] += 1
            self._stats['current_sessions'] = len(self.sessions)

        # Periodic cleanup
        self._maybe_cleanup()
    
    def delete(self, session_id: str):
        """Delete session data."""
        if session_id in self.sessions:
            self.sessions.pop(session_id, None)
            self._stats['total_sessions_deleted'] += 1
            self._stats['current_sessions'] = len(self.sessions)
    
    def cleanup(self):
        """Clean up expired sessions."""
        current_time = time.time()
        expired_sessions = [
            session_id for session_id, session_data in self.sessions.items()
            if session_data.get('_expires', 0) < current_time
        ]

        expired_count = len(expired_sessions)
        for session_id in expired_sessions:
            self.sessions.pop(session_id, None)

        self._stats['total_sessions_expired'] += expired_count
        self._stats['current_sessions'] = len(self.sessions)
        self._stats['cleanup_runs'] += 1
        self._last_cleanup = current_time

    def _maybe_cleanup(self):
        """Perform cleanup if interval has passed."""
        if time.time() - self._last_cleanup > self.cleanup_interval:
            self.cleanup()

    def _cleanup_oldest_sessions(self, count: int = None):
        """Remove oldest sessions to make room for new ones."""
        if count is None:
            count = max(1, self.max_sessions // 10)  # Remove 10% of sessions

        # Sort by last accessed time
        sorted_sessions = sorted(
            self.sessions.items(),
            key=lambda x: x[1].get('_last_accessed', 0)
        )

        for i in range(min(count, len(sorted_sessions))):
            session_id = sorted_sessions[i][0]
            self.sessions.pop(session_id, None)
            self._stats['total_sessions_deleted'] += 1

        self._stats['current_sessions'] = len(self.sessions)

    def get_stats(self) -> Dict[str, Any]:
        """Get session store statistics."""
        return {
            **self._stats,
            'memory_usage_estimate': len(self.sessions) * 1024,  # Rough estimate
            'max_sessions': self.max_sessions,
            'cleanup_interval': self.cleanup_interval
        }


class FileSessionStore(SessionStore):
    """
    File-based session storage.
    
    Stores session data in individual files on disk.
    """
    
    def __init__(self, session_dir: str = 'sessions'):
        """
        Initialize file session store.
        
        Args:
            session_dir: Directory to store session files
        """
        import os
        self.session_dir = session_dir
        os.makedirs(session_dir, exist_ok=True)
    
    def _get_session_file(self, session_id: str) -> str:
        """Get the file path for a session."""
        import os
        return os.path.join(self.session_dir, f"session_{session_id}.json")
    
    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data by ID."""
        import os
        
        session_file = self._get_session_file(session_id)
        if not os.path.exists(session_file):
            return None
        
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            # Check expiration
            if session_data.get('_expires', 0) < time.time():
                self.delete(session_id)
                return None
            
            return session_data.get('data', {})
            
        except (json.JSONDecodeError, IOError):
            # Corrupted or unreadable session file
            self.delete(session_id)
            return None
    
    def set(self, session_id: str, data: Dict[str, Any], expires: int = None):
        """Set session data."""
        if expires is None:
            expires = int(time.time()) + 3600  # 1 hour default
        
        session_data = {
            'data': data,
            '_expires': expires,
            '_created': time.time()
        }
        
        session_file = self._get_session_file(session_id)
        try:
            with open(session_file, 'w') as f:
                json.dump(session_data, f)
        except IOError:
            # Failed to write session file
            pass
    
    def delete(self, session_id: str):
        """Delete session data."""
        import os
        
        session_file = self._get_session_file(session_id)
        try:
            os.remove(session_file)
        except OSError:
            # File doesn't exist or can't be removed
            pass
    
    def cleanup(self):
        """Clean up expired sessions."""
        import os
        import glob
        
        current_time = time.time()
        session_files = glob.glob(os.path.join(self.session_dir, "session_*.json"))
        
        for session_file in session_files:
            try:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                
                if session_data.get('_expires', 0) < current_time:
                    os.remove(session_file)

            except (json.JSONDecodeError, IOError, OSError):
                # Remove corrupted or unreadable files
                try:
                    os.remove(session_file)
                except OSError:
                    pass


class SQLiteSessionStore(SessionStore):
    """
    SQLite-based session storage for better performance and persistence.

    This provides better performance than file-based storage and supports
    concurrent access with proper locking.
    """

    def __init__(self, db_path: str = 'sessions.db'):
        """
        Initialize SQLite session store.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_database()

        # Performance monitoring
        self._stats = {
            'total_sessions_created': 0,
            'total_sessions_expired': 0,
            'total_sessions_deleted': 0,
            'cleanup_runs': 0,
            'database_size_mb': 0.0
        }

    def _init_database(self):
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    expires INTEGER NOT NULL,
                    created INTEGER NOT NULL,
                    last_accessed INTEGER NOT NULL
                )
            ''')

            # Create index for faster cleanup
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_sessions_expires
                ON sessions(expires)
            ''')

            conn.commit()

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data by ID."""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(
                        'SELECT data, expires FROM sessions WHERE session_id = ?',
                        (session_id,)
                    )
                    row = cursor.fetchone()

                    if not row:
                        return None

                    data_json, expires = row

                    # Check expiration
                    if expires < time.time():
                        self.delete(session_id)
                        return None

                    # Update last accessed time
                    conn.execute(
                        'UPDATE sessions SET last_accessed = ? WHERE session_id = ?',
                        (time.time(), session_id)
                    )
                    conn.commit()

                    return json.loads(data_json)

            except (sqlite3.Error, json.JSONDecodeError):
                return None

    def set(self, session_id: str, data: Dict[str, Any], expires: int = None):
        """Set session data."""
        if expires is None:
            expires = int(time.time()) + 3600  # 1 hour default

        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    current_time = time.time()
                    data_json = json.dumps(data)

                    # Check if session exists
                    cursor = conn.execute(
                        'SELECT session_id FROM sessions WHERE session_id = ?',
                        (session_id,)
                    )
                    exists = cursor.fetchone() is not None

                    if exists:
                        conn.execute('''
                            UPDATE sessions
                            SET data = ?, expires = ?, last_accessed = ?
                            WHERE session_id = ?
                        ''', (data_json, expires, current_time, session_id))
                    else:
                        conn.execute('''
                            INSERT INTO sessions
                            (session_id, data, expires, created, last_accessed)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (session_id, data_json, expires, current_time, current_time))

                        self._stats['total_sessions_created'] += 1

                    conn.commit()

            except sqlite3.Error:
                pass  # Failed to save session

    def delete(self, session_id: str):
        """Delete session data."""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(
                        'DELETE FROM sessions WHERE session_id = ?',
                        (session_id,)
                    )
                    if cursor.rowcount > 0:
                        self._stats['total_sessions_deleted'] += 1
                    conn.commit()

            except sqlite3.Error:
                pass

    def cleanup(self):
        """Clean up expired sessions."""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    current_time = time.time()
                    cursor = conn.execute(
                        'DELETE FROM sessions WHERE expires < ?',
                        (current_time,)
                    )
                    expired_count = cursor.rowcount

                    # Vacuum database to reclaim space
                    conn.execute('VACUUM')
                    conn.commit()

                    self._stats['total_sessions_expired'] += expired_count
                    self._stats['cleanup_runs'] += 1

            except sqlite3.Error:
                pass

    def get_stats(self) -> Dict[str, Any]:
        """Get session store statistics."""
        # Calculate database size
        try:
            import os
            if os.path.exists(self.db_path):
                size_bytes = os.path.getsize(self.db_path)
                self._stats['database_size_mb'] = size_bytes / (1024 * 1024)
        except OSError:
            pass

        # Get current session count
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('SELECT COUNT(*) FROM sessions')
                current_sessions = cursor.fetchone()[0]
                self._stats['current_sessions'] = current_sessions
        except sqlite3.Error:
            pass

        return self._stats.copy()


class RedisSessionStore(SessionStore):
    """
    Redis-based session storage for high-performance distributed applications.

    Note: Requires redis-py package to be installed.
    """

    def __init__(self, redis_url: str = 'redis://localhost:6379/0',
                 key_prefix: str = 'foxpy:session:'):
        """
        Initialize Redis session store.

        Args:
            redis_url: Redis connection URL
            key_prefix: Prefix for session keys
        """
        try:
            import redis
            self.redis = redis.from_url(redis_url)
            self.key_prefix = key_prefix

            # Test connection
            self.redis.ping()

        except ImportError:
            raise ImportError("redis package is required for RedisSessionStore")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}")

    def _get_key(self, session_id: str) -> str:
        """Get Redis key for session ID."""
        return f"{self.key_prefix}{session_id}"

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data by ID."""
        try:
            key = self._get_key(session_id)
            data_json = self.redis.get(key)

            if not data_json:
                return None

            return json.loads(data_json.decode('utf-8'))

        except Exception:
            return None

    def set(self, session_id: str, data: Dict[str, Any], expires: int = None):
        """Set session data."""
        try:
            key = self._get_key(session_id)
            data_json = json.dumps(data)

            if expires:
                ttl = expires - int(time.time())
                if ttl > 0:
                    self.redis.setex(key, ttl, data_json)
            else:
                self.redis.set(key, data_json)

        except Exception:
            pass  # Failed to save session

    def delete(self, session_id: str):
        """Delete session data."""
        try:
            key = self._get_key(session_id)
            self.redis.delete(key)
        except Exception:
            pass

    def cleanup(self):
        """Clean up expired sessions (Redis handles this automatically)."""
        pass  # Redis handles expiration automatically


class SessionInterface:
    """
    Session interface for request/response handling.
    
    Provides a dict-like interface for session data.
    """
    
    def __init__(self, session_id: str, store: SessionStore):
        """
        Initialize session interface.
        
        Args:
            session_id: Session identifier
            store: Session storage backend
        """
        self.session_id = session_id
        self.store = store
        self._data = store.get(session_id) or {}
        self._modified = False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a session value."""
        return self._data.get(key, default)
    
    def __getitem__(self, key: str) -> Any:
        """Get a session value using dict syntax."""
        return self._data[key]
    
    def __setitem__(self, key: str, value: Any):
        """Set a session value using dict syntax."""
        self._data[key] = value
        self._modified = True
    
    def __delitem__(self, key: str):
        """Delete a session value using dict syntax."""
        del self._data[key]
        self._modified = True
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists in session."""
        return key in self._data
    
    def pop(self, key: str, default: Any = None) -> Any:
        """Remove and return a session value."""
        self._modified = True
        return self._data.pop(key, default)
    
    def clear(self):
        """Clear all session data."""
        self._data.clear()
        self._modified = True
    
    def save(self, expires: int = None):
        """Save session data to store."""
        if self._modified:
            self.store.set(self.session_id, self._data, expires)
            self._modified = False
    
    def destroy(self):
        """Destroy the session."""
        self.store.delete(self.session_id)
        self._data.clear()
        self._modified = False


class Session:
    """
    Session manager for FoxPy applications.
    
    Handles session creation, loading, and persistence.
    """
    
    def __init__(self, 
                 secret_key: str,
                 store: SessionStore = None,
                 cookie_name: str = 'foxpy_session',
                 cookie_domain: str = None,
                 cookie_path: str = '/',
                 cookie_secure: bool = False,
                 cookie_httponly: bool = True,
                 cookie_samesite: str = 'Lax',
                 session_lifetime: int = 3600):
        """
        Initialize session manager.
        
        Args:
            secret_key: Secret key for session signing
            store: Session storage backend
            cookie_name: Name of the session cookie
            cookie_domain: Cookie domain
            cookie_path: Cookie path
            cookie_secure: Whether cookie requires HTTPS
            cookie_httponly: Whether cookie is HTTP-only
            cookie_samesite: SameSite cookie attribute
            session_lifetime: Session lifetime in seconds
        """
        self.secret_key = secret_key
        self.store = store or MemorySessionStore()
        self.cookie_name = cookie_name
        self.cookie_domain = cookie_domain
        self.cookie_path = cookie_path
        self.cookie_secure = cookie_secure
        self.cookie_httponly = cookie_httponly
        self.cookie_samesite = cookie_samesite
        self.session_lifetime = session_lifetime
    
    def _generate_session_id(self) -> str:
        """Generate a new session ID."""
        return secrets.token_urlsafe(32)
    
    def _sign_session_id(self, session_id: str) -> str:
        """Sign a session ID to prevent tampering."""
        signature = hashlib.sha256(
            f"{session_id}:{self.secret_key}".encode('utf-8')
        ).hexdigest()[:16]
        return f"{session_id}.{signature}"
    
    def _verify_session_id(self, signed_session_id: str) -> Optional[str]:
        """Verify and extract session ID from signed value."""
        try:
            session_id, signature = signed_session_id.rsplit('.', 1)
            expected_signature = hashlib.sha256(
                f"{session_id}:{self.secret_key}".encode('utf-8')
            ).hexdigest()[:16]
            
            if signature == expected_signature:
                return session_id
        except ValueError:
            pass
        
        return None
    
    def load_session(self, request: Request) -> SessionInterface:
        """
        Load session from request.
        
        Args:
            request: HTTP request
            
        Returns:
            Session interface
        """
        # Get session ID from cookie
        signed_session_id = request.get_cookie(self.cookie_name)
        session_id = None
        
        if signed_session_id:
            session_id = self._verify_session_id(signed_session_id)
        
        if not session_id:
            # Create new session
            session_id = self._generate_session_id()
        
        return SessionInterface(session_id, self.store)
    
    def save_session(self, session: SessionInterface, response: Response):
        """
        Save session and set cookie in response.
        
        Args:
            session: Session interface
            response: HTTP response
        """
        # Save session data
        expires = int(time.time()) + self.session_lifetime
        session.save(expires)
        
        # Set session cookie
        signed_session_id = self._sign_session_id(session.session_id)
        response.set_cookie(
            self.cookie_name,
            signed_session_id,
            max_age=self.session_lifetime,
            path=self.cookie_path,
            domain=self.cookie_domain,
            secure=self.cookie_secure,
            httponly=self.cookie_httponly,
            samesite=self.cookie_samesite
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get session manager statistics."""
        store_stats = {}
        if hasattr(self.store, 'get_stats'):
            store_stats = self.store.get_stats()

        return {
            'store_type': type(self.store).__name__,
            'store_stats': store_stats,
            'cookie_name': self.cookie_name,
            'session_lifetime': self.session_lifetime,
            'cookie_secure': self.cookie_secure,
            'cookie_httponly': self.cookie_httponly,
            'cookie_samesite': self.cookie_samesite
        }


class AdvancedSession(Session):
    """
    Advanced session manager with additional security and features.

    Includes support for:
    - Session fingerprinting
    - Multi-factor authentication tracking
    - Session hijacking detection
    - Advanced security features
    """

    def __init__(self, *args, **kwargs):
        """Initialize advanced session manager."""
        # Extract advanced parameters before calling parent
        self.enable_fingerprinting = kwargs.pop('enable_fingerprinting', True)
        self.enable_hijack_detection = kwargs.pop('enable_hijack_detection', True)
        self.max_session_age = kwargs.pop('max_session_age', 86400)  # 24 hours
        self.require_mfa_for_sensitive = kwargs.pop('require_mfa_for_sensitive', False)

        # Call parent constructor with remaining kwargs
        super().__init__(*args, **kwargs)

        # Session security tracking
        self._security_stats = {
            'hijack_attempts_detected': 0,
            'fingerprint_mismatches': 0,
            'mfa_challenges_issued': 0,
            'suspicious_activities': 0
        }

    def _generate_fingerprint(self, request: Request) -> str:
        """
        Generate session fingerprint based on request characteristics.

        Args:
            request: HTTP request

        Returns:
            Session fingerprint hash
        """
        if not self.enable_fingerprinting:
            return ""

        # Collect fingerprint data
        fingerprint_data = [
            request.headers.get('User-Agent', ''),
            request.headers.get('Accept-Language', ''),
            request.headers.get('Accept-Encoding', ''),
            request.remote_addr or '',
        ]

        # Create fingerprint hash
        fingerprint_string = '|'.join(fingerprint_data)
        return hashlib.sha256(fingerprint_string.encode('utf-8')).hexdigest()[:16]

    def _detect_session_hijacking(self, session: 'AdvancedSessionInterface',
                                 request: Request) -> bool:
        """
        Detect potential session hijacking attempts.

        Args:
            session: Session interface
            request: HTTP request

        Returns:
            True if hijacking is suspected
        """
        if not self.enable_hijack_detection:
            return False

        # Check fingerprint mismatch
        current_fingerprint = self._generate_fingerprint(request)
        stored_fingerprint = session.get('_fingerprint', '')

        if stored_fingerprint and current_fingerprint != stored_fingerprint:
            self._security_stats['fingerprint_mismatches'] += 1
            return True

        # Check for rapid IP changes
        current_ip = request.remote_addr
        stored_ip = session.get('_last_ip', '')
        last_ip_change = session.get('_last_ip_change', 0)

        if (stored_ip and current_ip != stored_ip and
            time.time() - last_ip_change < 300):  # 5 minutes
            self._security_stats['suspicious_activities'] += 1
            return True

        return False

    def load_session(self, request: Request) -> 'AdvancedSessionInterface':
        """
        Load session with advanced security checks.

        Args:
            request: HTTP request

        Returns:
            Advanced session interface
        """
        # Get basic session
        signed_session_id = request.get_cookie(self.cookie_name)
        session_id = None

        if signed_session_id:
            session_id = self._verify_session_id(signed_session_id)

        if not session_id:
            # Create new session
            session_id = self._generate_session_id()

        session = AdvancedSessionInterface(session_id, self.store, self)

        # Security checks for existing sessions
        if session._data:
            # Check session age
            created_time = session.get('_created', time.time())
            if time.time() - created_time > self.max_session_age:
                session.destroy()
                session = AdvancedSessionInterface(
                    self._generate_session_id(), self.store, self
                )

            # Check for hijacking
            elif self._detect_session_hijacking(session, request):
                self._security_stats['hijack_attempts_detected'] += 1
                session.destroy()
                session = AdvancedSessionInterface(
                    self._generate_session_id(), self.store, self
                )

        # Set security metadata
        session['_fingerprint'] = self._generate_fingerprint(request)
        session['_last_ip'] = request.remote_addr
        session['_last_access'] = time.time()

        if '_created' not in session:
            session['_created'] = time.time()

        return session

    def require_mfa(self, session: 'AdvancedSessionInterface') -> bool:
        """
        Check if multi-factor authentication is required.

        Args:
            session: Session interface

        Returns:
            True if MFA is required
        """
        if not self.require_mfa_for_sensitive:
            return False

        # Check if MFA was recently completed
        mfa_timestamp = session.get('_mfa_verified', 0)
        mfa_validity = 3600  # 1 hour

        if time.time() - mfa_timestamp > mfa_validity:
            self._security_stats['mfa_challenges_issued'] += 1
            return True

        return False

    def verify_mfa(self, session: 'AdvancedSessionInterface'):
        """
        Mark MFA as verified for the session.

        Args:
            session: Session interface
        """
        session['_mfa_verified'] = time.time()

    def get_security_stats(self) -> Dict[str, Any]:
        """Get security-related statistics."""
        return self._security_stats.copy()


class AdvancedSessionInterface(SessionInterface):
    """
    Advanced session interface with additional security features.
    """

    def __init__(self, session_id: str, store: SessionStore,
                 session_manager: AdvancedSession):
        """
        Initialize advanced session interface.

        Args:
            session_id: Session identifier
            store: Session storage backend
            session_manager: Advanced session manager
        """
        super().__init__(session_id, store)
        self.session_manager = session_manager

    def is_mfa_required(self) -> bool:
        """Check if MFA is required for this session."""
        return self.session_manager.require_mfa(self)

    def verify_mfa(self):
        """Mark MFA as verified for this session."""
        self.session_manager.verify_mfa(self)

    def get_security_info(self) -> Dict[str, Any]:
        """Get security information for this session."""
        return {
            'fingerprint': self.get('_fingerprint', ''),
            'last_ip': self.get('_last_ip', ''),
            'created': self.get('_created', 0),
            'last_access': self.get('_last_access', 0),
            'mfa_verified': self.get('_mfa_verified', 0),
            'session_age': time.time() - self.get('_created', time.time())
        }


class AdvancedSessionInterface:
    """
    Advanced session interface with enterprise security features.
    """

    def __init__(self, store: SessionStore, secret_key: str,
                 enable_fingerprinting: bool = True,
                 enable_hijack_detection: bool = True,
                 max_session_age: int = 86400):
        """
        Initialize advanced session interface.

        Args:
            store: Session storage backend
            secret_key: Secret key for session security
            enable_fingerprinting: Enable device fingerprinting
            enable_hijack_detection: Enable session hijacking detection
            max_session_age: Maximum session age in seconds
        """
        self.store = store
        self.secret_key = secret_key
        self.enable_fingerprinting = enable_fingerprinting
        self.enable_hijack_detection = enable_hijack_detection
        self.max_session_age = max_session_age

        # Security monitoring
        self._security_events = deque(maxlen=1000)
        self._suspicious_ips = set()
        self._failed_attempts = defaultdict(int)

        # Session analytics
        self._session_analytics = {
            'total_sessions': 0,
            'active_sessions': 0,
            'hijack_attempts': 0,
            'mfa_sessions': 0,
            'security_violations': 0
        }

    def create_session(self, request: Request, user_id: str = None) -> str:
        """
        Create a new secure session with enhanced security features.

        Args:
            request: HTTP request object
            user_id: Optional user ID to associate with session

        Returns:
            Session ID
        """
        session_id = self._generate_secure_session_id()

        # Create session data with enhanced security metadata
        session_data = {
            'user_id': user_id,
            '_created': time.time(),
            '_last_access': time.time(),
            '_ip': request.remote_addr,
            '_user_agent': request.headers.get('User-Agent', ''),
            '_csrf_token': secrets.token_urlsafe(32),
            '_mfa_verified': 0,
            '_security_level': 'standard',
            '_rotation_count': 0,
            '_last_rotation': time.time(),
            '_access_count': 0,
            '_suspicious_activity': False,
            '_login_attempts': 0,
            '_last_login_attempt': None
        }

        # Add device fingerprint if enabled
        if self.enable_fingerprinting:
            session_data['_fingerprint'] = self._generate_fingerprint(request)

        # Store session
        expires = int(time.time()) + self.max_session_age
        self.store.set(session_id, session_data, expires)

        # Update analytics
        self._session_analytics['total_sessions'] += 1
        self._session_analytics['active_sessions'] += 1

        return session_id

    def validate_session(self, request: Request, session_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate session with advanced security checks.

        Args:
            request: HTTP request object
            session_id: Session ID to validate

        Returns:
            Tuple of (is_valid, session_data or security_info)
        """
        # Get session data
        session_data = self.store.get(session_id)
        if not session_data:
            return False, {'error': 'session_not_found'}

        # Check session age
        session_age = time.time() - session_data.get('_created', 0)
        if session_age > self.max_session_age:
            self.store.delete(session_id)
            return False, {'error': 'session_expired'}

        # IP address validation
        current_ip = request.remote_addr
        session_ip = session_data.get('_ip', '')

        if self.enable_hijack_detection and current_ip != session_ip:
            # Check if IP change is suspicious
            if self._is_suspicious_ip_change(session_ip, current_ip):
                self._record_security_event('ip_hijack_attempt', {
                    'session_id': session_id,
                    'original_ip': session_ip,
                    'new_ip': current_ip,
                    'user_agent': request.headers.get('User-Agent', '')
                })
                return False, {'error': 'suspicious_ip_change'}

        # Device fingerprint validation
        if self.enable_fingerprinting:
            current_fingerprint = self._generate_fingerprint(request)
            session_fingerprint = session_data.get('_fingerprint', '')

            if current_fingerprint != session_fingerprint:
                self._record_security_event('fingerprint_mismatch', {
                    'session_id': session_id,
                    'expected': session_fingerprint,
                    'actual': current_fingerprint
                })
                return False, {'error': 'device_fingerprint_mismatch'}

        # Update last access
        session_data['_last_access'] = time.time()
        session_data['_ip'] = current_ip  # Update IP for legitimate changes

        expires = int(time.time()) + self.max_session_age
        self.store.set(session_id, session_data, expires)

        return True, session_data

    def _generate_secure_session_id(self) -> str:
        """Generate cryptographically secure session ID."""
        # Combine multiple entropy sources
        entropy = secrets.token_bytes(32)
        timestamp = str(time.time()).encode()
        random_data = secrets.token_bytes(16)

        # Create HMAC-based session ID
        combined = entropy + timestamp + random_data
        session_id = hmac.new(
            self.secret_key.encode(),
            combined,
            hashlib.sha256
        ).hexdigest()

        return session_id

    def _generate_fingerprint(self, request: Request) -> str:
        """Generate device fingerprint from request."""
        fingerprint_data = [
            request.headers.get('User-Agent', ''),
            request.headers.get('Accept-Language', ''),
            request.headers.get('Accept-Encoding', ''),
            request.headers.get('Accept', ''),
            request.remote_addr,
            # Add more headers as needed for fingerprinting
        ]

        fingerprint_string = '|'.join(fingerprint_data)
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()

    def _is_suspicious_ip_change(self, old_ip: str, new_ip: str) -> bool:
        """Check if IP change is suspicious."""
        try:
            old_addr = ipaddress.ip_address(old_ip)
            new_addr = ipaddress.ip_address(new_ip)

            # Allow changes within same subnet (less suspicious)
            if old_addr.version == new_addr.version:
                if old_addr.version == 4:
                    # Allow /24 subnet changes for IPv4
                    old_network = ipaddress.IPv4Network(f"{old_ip}/24", strict=False)
                    return new_addr not in old_network
                else:
                    # Allow /64 subnet changes for IPv6
                    old_network = ipaddress.IPv6Network(f"{old_ip}/64", strict=False)
                    return new_addr not in old_network

            return True  # Different IP versions are suspicious

        except ValueError:
            return True  # Invalid IP addresses are suspicious

    def _record_security_event(self, event_type: str, details: Dict[str, Any]):
        """Record security event for monitoring."""
        event = {
            'type': event_type,
            'timestamp': time.time(),
            'details': details
        }

        self._security_events.append(event)
        self._session_analytics['security_violations'] += 1

        # Add IP to suspicious list for certain events
        if event_type in ['ip_hijack_attempt', 'fingerprint_mismatch']:
            if 'new_ip' in details:
                self._suspicious_ips.add(details['new_ip'])

    def get_security_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent security events."""
        return list(self._security_events)[-limit:]

    def get_session_analytics(self) -> Dict[str, Any]:
        """Get session analytics and security metrics."""
        return {
            **self._session_analytics,
            'suspicious_ips_count': len(self._suspicious_ips),
            'recent_events_count': len(self._security_events)
        }

    def rotate_session(self, old_session_id: str, request: Request) -> str:
        """
        Rotate session ID for security (prevents session fixation attacks).

        Args:
            old_session_id: Current session ID
            request: HTTP request object

        Returns:
            New session ID
        """
        # Get existing session data
        session_data = self.store.get(old_session_id)
        if not session_data:
            return self.create_session(request)

        # Generate new session ID
        new_session_id = self._generate_secure_session_id()

        # Update session metadata
        session_data['_rotation_count'] = session_data.get('_rotation_count', 0) + 1
        session_data['_last_rotation'] = time.time()
        session_data['_last_access'] = time.time()

        # Store with new ID
        expires = int(time.time()) + self.max_session_age
        self.store.set(new_session_id, session_data, expires)

        # Remove old session
        self.store.delete(old_session_id)

        # Log rotation for security monitoring
        self._log_security_event('session_rotated', {
            'old_session_id': old_session_id[:8] + '...',  # Partial ID for privacy
            'new_session_id': new_session_id[:8] + '...',
            'user_id': session_data.get('user_id'),
            'ip': request.remote_addr,
            'rotation_count': session_data['_rotation_count']
        })

        return new_session_id

    def detect_session_anomalies(self, session_id: str, request: Request) -> List[str]:
        """
        Detect potential session security anomalies.

        Args:
            session_id: Session ID to check
            request: Current request

        Returns:
            List of detected anomalies
        """
        anomalies = []
        session_data = self.store.get(session_id)

        if not session_data:
            return ['session_not_found']

        # Check IP address changes
        stored_ip = session_data.get('_ip')
        current_ip = request.remote_addr
        if stored_ip and stored_ip != current_ip:
            anomalies.append('ip_address_changed')

        # Check user agent changes
        stored_ua = session_data.get('_user_agent')
        current_ua = request.headers.get('User-Agent', '')
        if stored_ua and stored_ua != current_ua:
            anomalies.append('user_agent_changed')

        # Check for rapid access patterns
        last_access = session_data.get('_last_access', 0)
        if time.time() - last_access < 1:  # Less than 1 second
            access_count = session_data.get('_access_count', 0)
            if access_count > 10:  # More than 10 requests per second
                anomalies.append('rapid_access_pattern')

        # Check session age
        created = session_data.get('_created', 0)
        if time.time() - created > self.max_session_age:
            anomalies.append('session_expired')

        # Check for excessive rotations
        rotation_count = session_data.get('_rotation_count', 0)
        if rotation_count > 10:  # More than 10 rotations
            anomalies.append('excessive_rotations')

        return anomalies
