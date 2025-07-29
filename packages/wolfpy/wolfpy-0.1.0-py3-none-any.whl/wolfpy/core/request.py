"""
WolfPy Request Module.

This module provides enhanced HTTP request handling and parsing functionality
with improved security, validation, and developer experience.
"""

import json
import urllib.parse
import tempfile
import re
from typing import Dict, Any, Optional, List, Union, NamedTuple, Callable
from io import StringIO, BytesIO
from datetime import datetime
from decimal import Decimal, InvalidOperation


class FileUpload(NamedTuple):
    """Represents an uploaded file."""
    filename: str
    content_type: str
    content: bytes

    def save(self, path: str) -> None:
        """Save the uploaded file to disk."""
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(self.content)

    def save_secure(self, upload_folder: str, allowed_extensions: set = None) -> str:
        """
        Save file securely with validation.

        Args:
            upload_folder: Directory to save file
            allowed_extensions: Set of allowed file extensions

        Returns:
            Path where file was saved

        Raises:
            ValueError: If file is invalid or extension not allowed
        """
        import os
        import secrets
        from pathlib import Path

        if self.is_empty:
            raise ValueError("Cannot save empty file")

        # Validate file extension
        if allowed_extensions:
            file_ext = Path(self.filename).suffix.lower()
            if file_ext not in allowed_extensions:
                raise ValueError(f"File extension {file_ext} not allowed")

        # Generate secure filename
        secure_filename = self._secure_filename(self.filename)
        if not secure_filename:
            secure_filename = f"upload_{secrets.token_hex(8)}"

        # Ensure unique filename
        save_path = os.path.join(upload_folder, secure_filename)
        counter = 1
        while os.path.exists(save_path):
            name, ext = os.path.splitext(secure_filename)
            save_path = os.path.join(upload_folder, f"{name}_{counter}{ext}")
            counter += 1

        # Save file
        os.makedirs(upload_folder, exist_ok=True)
        with open(save_path, 'wb') as f:
            f.write(self.content)

        return save_path

    def _secure_filename(self, filename: str) -> str:
        """Generate secure filename."""
        import re
        import unicodedata

        # Normalize unicode
        filename = unicodedata.normalize('NFKD', filename)

        # Remove non-ASCII characters
        filename = filename.encode('ascii', 'ignore').decode('ascii')

        # Remove dangerous characters
        filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)

        # Remove leading dots and spaces
        filename = filename.lstrip('. ')

        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext

        return filename

    @property
    def size(self) -> int:
        """Get file size in bytes."""
        return len(self.content)

    @property
    def is_empty(self) -> bool:
        """Check if file is empty."""
        return len(self.content) == 0

    @property
    def extension(self) -> str:
        """Get file extension."""
        import os
        return os.path.splitext(self.filename)[1].lower()

    def is_image(self) -> bool:
        """Check if file is an image."""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}
        return self.extension in image_extensions

    def validate_image(self, max_size: int = None) -> bool:
        """
        Validate image file.

        Args:
            max_size: Maximum file size in bytes

        Returns:
            True if valid image, False otherwise
        """
        if not self.is_image():
            return False

        if max_size and self.size > max_size:
            return False

        # Basic image validation by checking magic bytes
        if self.content.startswith(b'\xff\xd8\xff'):  # JPEG
            return True
        elif self.content.startswith(b'\x89PNG\r\n\x1a\n'):  # PNG
            return True
        elif self.content.startswith(b'GIF8'):  # GIF
            return True
        elif self.content.startswith(b'BM'):  # BMP
            return True

        return False


class RequestValidator:
    """Request data validation utilities."""

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format."""
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, url))

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number format."""
        pattern = r'^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$'
        return bool(re.match(pattern, phone))

    @staticmethod
    def sanitize_string(value: str, max_length: int = None) -> str:
        """Sanitize string input with HTML escaping."""
        if not isinstance(value, str):
            return str(value)

        # HTML escape dangerous characters
        sanitized = value.replace('&', '&amp;')
        sanitized = sanitized.replace('<', '&lt;')
        sanitized = sanitized.replace('>', '&gt;')
        sanitized = sanitized.replace('"', '&quot;')
        sanitized = sanitized.replace("'", '&#x27;')

        # Remove null bytes and control characters
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\t\n\r')

        if max_length:
            sanitized = sanitized[:max_length]

        return sanitized.strip()


class RequestParser:
    """Advanced request parsing utilities."""

    @staticmethod
    def parse_accept_header(accept_header: str) -> List[Dict[str, Any]]:
        """Parse Accept header into prioritized list."""
        if not accept_header:
            return []

        media_types = []
        for item in accept_header.split(','):
            item = item.strip()
            if ';' in item:
                media_type, params = item.split(';', 1)
                quality = 1.0
                for param in params.split(';'):
                    param = param.strip()
                    if param.startswith('q='):
                        try:
                            quality = float(param[2:])
                        except ValueError:
                            quality = 1.0
                        break
            else:
                media_type = item
                quality = 1.0

            media_types.append({
                'media_type': media_type.strip(),
                'quality': quality
            })

        # Sort by quality (highest first)
        return sorted(media_types, key=lambda x: x['quality'], reverse=True)

    @staticmethod
    def parse_content_type(content_type: str) -> Dict[str, str]:
        """Parse Content-Type header."""
        if not content_type:
            return {'type': '', 'charset': 'utf-8', 'boundary': ''}

        parts = content_type.split(';')
        result = {'type': parts[0].strip(), 'charset': 'utf-8', 'boundary': ''}

        for part in parts[1:]:
            part = part.strip()
            if '=' in part:
                key, value = part.split('=', 1)
                result[key.strip()] = value.strip().strip('"')

        return result


class Request:
    """
    Enhanced HTTP Request object for WolfPy applications.

    Provides access to request data including:
    - URL parameters and query strings
    - Form data and JSON payloads
    - Headers and cookies
    - File uploads
    - Request validation and sanitization
    - Content negotiation
    - Security features
    """
    
    def __init__(self, environ: Dict[str, Any]):
        """
        Initialize request from WSGI environ.

        Args:
            environ: WSGI environment dictionary
        """
        self.environ = environ
        self._form_data = None
        self._json_data = None
        self._files = None
        self._parsed_content_type = None
        self._accept_types = None
        self._cookies = None
        self._context = {}  # Request-scoped context data
        self.validator = RequestValidator()
        self.parser = RequestParser()
        
    @property
    def method(self) -> str:
        """Get the HTTP method (GET, POST, etc.)."""
        return self.environ.get('REQUEST_METHOD', 'GET').upper()
    
    @property
    def path(self) -> str:
        """Get the request path."""
        return self.environ.get('PATH_INFO', '/')
    
    @property
    def query_string(self) -> str:
        """Get the raw query string."""
        return self.environ.get('QUERY_STRING', '')
    
    @property
    def url(self) -> str:
        """Get the full request URL."""
        scheme = self.environ.get('wsgi.url_scheme', 'http')
        host = self.environ.get('HTTP_HOST') or self.environ.get('SERVER_NAME', 'localhost')
        port = self.environ.get('SERVER_PORT', '80')
        
        if (scheme == 'http' and port != '80') or (scheme == 'https' and port != '443'):
            host = f"{host}:{port}"
        
        return f"{scheme}://{host}{self.path}"
    
    @property
    def headers(self) -> Dict[str, str]:
        """Get request headers."""
        headers = {}
        for key, value in self.environ.items():
            if key.startswith('HTTP_'):
                # Convert HTTP_CONTENT_TYPE to Content-Type
                header_name = key[5:].replace('_', '-').title()
                headers[header_name] = value
            elif key in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                # These don't have HTTP_ prefix
                header_name = key.replace('_', '-').title()
                headers[header_name] = value
        return headers
    
    @property
    def content_type(self) -> str:
        """Get the content type header."""
        return self.environ.get('CONTENT_TYPE', '')
    
    @property
    def content_length(self) -> int:
        """Get the content length."""
        try:
            return int(self.environ.get('CONTENT_LENGTH', 0))
        except (ValueError, TypeError):
            return 0
    
    @property
    def args(self) -> Dict[str, List[str]]:
        """Get query string parameters as a dict of lists."""
        if not self.query_string:
            return {}
        
        parsed = urllib.parse.parse_qs(self.query_string, keep_blank_values=True)
        return parsed
    
    def get_arg(self, key: str, default: Any = None, type_cast: Callable = None) -> Any:
        """
        Get a single query parameter value with optional type casting.

        Args:
            key: Parameter name
            default: Default value if not found
            type_cast: Function to cast the value (e.g., int, float)

        Returns:
            Parameter value (optionally cast) or default
        """
        values = self.args.get(key, [])
        if not values:
            return default

        value = values[0]
        if type_cast:
            try:
                return type_cast(value)
            except (ValueError, TypeError):
                return default

        return value

    def get_args_list(self, key: str, type_cast: Callable = None) -> List[Any]:
        """
        Get all values for a query parameter as a list.

        Args:
            key: Parameter name
            type_cast: Function to cast values

        Returns:
            List of parameter values
        """
        values = self.args.get(key, [])
        if not type_cast:
            return values

        result = []
        for value in values:
            try:
                result.append(type_cast(value))
            except (ValueError, TypeError):
                continue

        return result

    def get_int(self, key: str, default: int = None) -> Optional[int]:
        """Get query parameter as integer."""
        return self.get_arg(key, default, int)

    def get_float(self, key: str, default: float = None) -> Optional[float]:
        """Get query parameter as float."""
        return self.get_arg(key, default, float)

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get query parameter as boolean."""
        value = self.get_arg(key)
        if value is None:
            return default
        return value.lower() in ('true', '1', 'yes', 'on')
    
    @property
    def form(self) -> Dict[str, List[str]]:
        """Get form data as a dict of lists."""
        if self._form_data is None:
            self._parse_form_data()
        return self._form_data or {}
    
    def get_form(self, key: str, default: Any = None, type_cast: Callable = None,
                 sanitize: bool = True) -> Any:
        """
        Get a single form field value with optional type casting and sanitization.

        Args:
            key: Field name
            default: Default value if not found
            type_cast: Function to cast the value
            sanitize: Whether to sanitize string values

        Returns:
            Field value (optionally cast and sanitized) or default
        """
        values = self.form.get(key, [])
        if not values:
            return default

        value = values[0]

        # Sanitize string values
        if sanitize and isinstance(value, str):
            value = self.validator.sanitize_string(value)

        # Type casting
        if type_cast:
            try:
                return type_cast(value)
            except (ValueError, TypeError):
                return default

        return value

    def get_form_list(self, key: str, type_cast: Callable = None,
                      sanitize: bool = True) -> List[Any]:
        """
        Get all values for a form field as a list.

        Args:
            key: Field name
            type_cast: Function to cast values
            sanitize: Whether to sanitize string values

        Returns:
            List of field values
        """
        values = self.form.get(key, [])
        result = []

        for value in values:
            if sanitize and isinstance(value, str):
                value = self.validator.sanitize_string(value)

            if type_cast:
                try:
                    value = type_cast(value)
                except (ValueError, TypeError):
                    continue

            result.append(value)

        return result

    def get_form_int(self, key: str, default: int = None) -> Optional[int]:
        """Get form field as integer."""
        return self.get_form(key, default, int)

    def get_form_float(self, key: str, default: float = None) -> Optional[float]:
        """Get form field as float."""
        return self.get_form(key, default, float)

    def get_form_bool(self, key: str, default: bool = False) -> bool:
        """Get form field as boolean."""
        value = self.get_form(key)
        if value is None:
            return default
        return str(value).lower() in ('true', '1', 'yes', 'on', 'checked')

    def validate_form_field(self, key: str, validator_func: Callable) -> bool:
        """
        Validate a form field using a custom validator function.

        Args:
            key: Field name
            validator_func: Function that takes a value and returns bool

        Returns:
            True if valid, False otherwise
        """
        value = self.get_form(key)
        if value is None:
            return False

        try:
            return validator_func(value)
        except Exception:
            return False
    
    @property
    def json(self) -> Optional[Dict[str, Any]]:
        """Get JSON data from request body."""
        if self._json_data is None:
            self._parse_json_data()
        return self._json_data

    def get_json(self, key: str = None, default: Any = None, type_cast: Callable = None) -> Any:
        """
        Get JSON data or a specific key from JSON data.

        Args:
            key: JSON key to retrieve (None for entire JSON)
            default: Default value if key not found
            type_cast: Function to cast the value

        Returns:
            JSON data or specific value
        """
        json_data = self.json
        if json_data is None:
            return default

        if key is None:
            return json_data

        # Support nested keys with dot notation (e.g., "user.name")
        value = json_data
        for part in key.split('.'):
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default

        if type_cast:
            try:
                return type_cast(value)
            except (ValueError, TypeError):
                return default

        return value

    def validate_json_schema(self, schema: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validate JSON data against a simple schema.

        Args:
            schema: Schema definition with field requirements

        Returns:
            Dictionary of validation errors
        """
        errors = {}
        json_data = self.json

        if json_data is None:
            return {'_general': ['No JSON data provided']}

        for field, requirements in schema.items():
            value = json_data.get(field)
            field_errors = []

            # Required field check
            if requirements.get('required', False) and value is None:
                field_errors.append(f'{field} is required')

            if value is not None:
                # Type check
                expected_type = requirements.get('type')
                if expected_type and not isinstance(value, expected_type):
                    field_errors.append(f'{field} must be of type {expected_type.__name__}')

                # Min/max length for strings
                if isinstance(value, str):
                    min_length = requirements.get('min_length')
                    max_length = requirements.get('max_length')
                    if min_length and len(value) < min_length:
                        field_errors.append(f'{field} must be at least {min_length} characters')
                    if max_length and len(value) > max_length:
                        field_errors.append(f'{field} must be at most {max_length} characters')

                # Custom validator
                validator = requirements.get('validator')
                if validator and not validator(value):
                    field_errors.append(f'{field} is invalid')

            if field_errors:
                errors[field] = field_errors

        return errors
    
    @property
    def data(self) -> bytes:
        """Get raw request body data."""
        try:
            content_length = self.content_length
            if content_length > 0:
                data = self.environ['wsgi.input'].read(content_length)
                # Handle both bytes and string data (for test compatibility)
                if isinstance(data, str):
                    return data.encode('utf-8')
                return data
        except (KeyError, ValueError):
            pass
        return b''
    
    @property
    def cookies(self) -> Dict[str, str]:
        """Get request cookies."""
        cookie_header = self.environ.get('HTTP_COOKIE', '')
        cookies = {}
        
        if cookie_header:
            for chunk in cookie_header.split(';'):
                if '=' in chunk:
                    key, value = chunk.strip().split('=', 1)
                    cookies[key] = urllib.parse.unquote(value)
        
        return cookies
    
    def get_cookie(self, key: str, default: Any = None) -> Optional[str]:
        """
        Get a cookie value.
        
        Args:
            key: Cookie name
            default: Default value if not found
            
        Returns:
            Cookie value or default
        """
        return self.cookies.get(key, default)
    
    @property
    def remote_addr(self) -> str:
        """Get client IP address."""
        # Check for forwarded headers first (proxy/load balancer)
        forwarded_for = self.environ.get('HTTP_X_FORWARDED_FOR')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = self.environ.get('HTTP_X_REAL_IP')
        if real_ip:
            return real_ip
        
        return self.environ.get('REMOTE_ADDR', '127.0.0.1')
    
    @property
    def user_agent(self) -> str:
        """Get user agent string."""
        return self.environ.get('HTTP_USER_AGENT', '')

    @property
    def files(self) -> Dict[str, List[FileUpload]]:
        """Get uploaded files as a dict of lists."""
        if self._files is None:
            self._parse_form_data()
        return self._files or {}

    def get_file(self, key: str) -> Optional[FileUpload]:
        """
        Get a single uploaded file.

        Args:
            key: Field name

        Returns:
            FileUpload object or None
        """
        files = self.files.get(key, [])
        return files[0] if files else None

    def _parse_form_data(self):
        """Parse form data from request body."""
        if self.method not in ('POST', 'PUT', 'PATCH'):
            self._form_data = {}
            self._files = {}
            return

        content_type = self.content_type.lower()

        if content_type.startswith('application/x-www-form-urlencoded'):
            try:
                body = self.data
                # Handle both bytes and string data
                if isinstance(body, bytes):
                    body = body.decode('utf-8')
                elif not isinstance(body, str):
                    body = str(body)

                self._form_data = urllib.parse.parse_qs(body, keep_blank_values=True)
                self._files = {}
            except (UnicodeDecodeError, AttributeError):
                self._form_data = {}
                self._files = {}
        elif content_type.startswith('multipart/form-data'):
            self._parse_multipart_data()
        else:
            self._form_data = {}
            self._files = {}

    def _parse_multipart_data(self):
        """Enhanced multipart form data parser with better error handling and validation."""
        self._form_data = {}
        self._files = {}

        content_type = self.environ.get('CONTENT_TYPE', '')
        if 'boundary=' not in content_type:
            return

        try:
            # Extract boundary with better parsing
            boundary_match = re.search(r'boundary=([^;]+)', content_type)
            if not boundary_match:
                return

            boundary = boundary_match.group(1).strip()
            if boundary.startswith('"') and boundary.endswith('"'):
                boundary = boundary[1:-1]

            body = self.data
            if not body:
                return

            boundary_bytes = ('--' + boundary).encode('utf-8')
            end_boundary_bytes = ('--' + boundary + '--').encode('utf-8')

            # Split by boundary with validation
            parts = body.split(boundary_bytes)

            # Remove empty first part and end boundary
            if parts and not parts[0].strip():
                parts = parts[1:]

            # Remove end boundary part
            if parts and end_boundary_bytes in parts[-1]:
                parts = parts[:-1]

            for part in parts[1:]:  # Skip first empty part
                if part.startswith(b'--'):  # End boundary
                    break

                if b'\r\n\r\n' not in part:
                    continue

                headers_section, content = part.split(b'\r\n\r\n', 1)
                content = content.rstrip(b'\r\n')

                # Parse headers with better error handling
                headers = {}
                try:
                    header_text = headers_section.decode('utf-8', errors='replace').strip()
                    for line in header_text.split('\r\n'):
                        line = line.strip()
                        if ':' in line:
                            key, value = line.split(':', 1)
                            headers[key.strip().lower()] = value.strip()
                except UnicodeDecodeError:
                    continue

                content_disposition = headers.get('content-disposition', '')
                if 'name=' not in content_disposition:
                    continue

                # Enhanced field name extraction with regex for better parsing
                name_match = re.search(r'name="([^"]*)"', content_disposition)
                if not name_match:
                    # Fallback to simple parsing
                    try:
                        name_match = content_disposition.split('name="')[1].split('"')[0]
                    except (IndexError, ValueError):
                        continue
                else:
                    name_match = name_match.group(1)

                # Check if it's a file upload
                filename_match = re.search(r'filename="([^"]*)"', content_disposition)
                if filename_match:
                    filename = filename_match.group(1)
                    content_type = headers.get('content-type', 'application/octet-stream')

                    # Validate file upload size (50MB limit)
                    if len(content) > 50 * 1024 * 1024:
                        continue  # Skip large files

                    file_upload = FileUpload(
                        filename=filename,
                        content_type=content_type,
                        content=content
                    )

                    if name_match not in self._files:
                        self._files[name_match] = []
                    self._files[name_match].append(file_upload)
                else:
                    # Regular form field with size validation
                    if len(content) > 1024 * 1024:  # 1MB limit for form fields
                        continue

                    try:
                        value = content.decode('utf-8', errors='replace')
                        if name_match not in self._form_data:
                            self._form_data[name_match] = []
                        self._form_data[name_match].append(value)
                    except Exception:
                        pass

        except Exception:
            # If parsing fails, return empty dicts
            self._form_data = {}
            self._files = {}
    
    def _parse_json_data(self):
        """Parse JSON data from request body."""
        if not self.content_type.startswith('application/json'):
            self._json_data = None
            return

        try:
            body = self.data
            # Handle both bytes and string data
            if isinstance(body, bytes):
                body = body.decode(self.charset)
            elif not isinstance(body, str):
                # Handle other types (like from StringIO in tests)
                body = str(body)

            self._json_data = json.loads(body) if body else None
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            self._json_data = None

    def _parse_cookies(self):
        """Parse cookies from request headers."""
        cookie_header = self.environ.get('HTTP_COOKIE', '')
        if not cookie_header:
            self._cookies = {}
            return

        cookies = {}
        for item in cookie_header.split(';'):
            item = item.strip()
            if '=' in item:
                name, value = item.split('=', 1)
                cookies[name.strip()] = urllib.parse.unquote(value.strip())

        self._cookies = cookies
    
    def is_json(self) -> bool:
        """Check if request contains JSON data."""
        return self.content_type.startswith('application/json')
    
    def is_ajax(self) -> bool:
        """Check if request is an AJAX request."""
        return self.environ.get('HTTP_X_REQUESTED_WITH', '').lower() == 'xmlhttprequest'

    @property
    def cookies(self) -> Dict[str, str]:
        """Get cookies from request."""
        if self._cookies is None:
            self._parse_cookies()
        return self._cookies or {}

    def get_cookie(self, name: str, default: str = None) -> Optional[str]:
        """Get a specific cookie value."""
        return self.cookies.get(name, default)

    @property
    def accept_types(self) -> List[Dict[str, Any]]:
        """Get accepted content types from Accept header."""
        if self._accept_types is None:
            accept_header = self.environ.get('HTTP_ACCEPT', '')
            self._accept_types = self.parser.parse_accept_header(accept_header)
        return self._accept_types

    def accepts(self, content_type: str) -> bool:
        """Check if client accepts a specific content type."""
        for accept_type in self.accept_types:
            if (accept_type['media_type'] == content_type or
                accept_type['media_type'] == '*/*' or
                accept_type['media_type'].split('/')[0] + '/*' == content_type):
                return True
        return False

    def prefers(self, *content_types: str) -> Optional[str]:
        """Get the preferred content type from a list of options."""
        for accept_type in self.accept_types:
            for content_type in content_types:
                if (accept_type['media_type'] == content_type or
                    accept_type['media_type'] == '*/*'):
                    return content_type
        return None

    @property
    def parsed_content_type(self) -> Dict[str, str]:
        """Get parsed Content-Type header."""
        if self._parsed_content_type is None:
            content_type = self.environ.get('CONTENT_TYPE', '')
            self._parsed_content_type = self.parser.parse_content_type(content_type)
        return self._parsed_content_type

    @property
    def charset(self) -> str:
        """Get request charset."""
        return self.parsed_content_type.get('charset', 'utf-8')

    @property
    def boundary(self) -> str:
        """Get multipart boundary."""
        return self.parsed_content_type.get('boundary', '')

    def get_header(self, name: str, default: str = None) -> Optional[str]:
        """Get a specific header value."""
        # Convert header name to WSGI format
        wsgi_name = 'HTTP_' + name.upper().replace('-', '_')
        return self.environ.get(wsgi_name, default)

    @property
    def authorization(self) -> Optional[str]:
        """Get Authorization header."""
        return self.environ.get('HTTP_AUTHORIZATION')

    @property
    def referrer(self) -> Optional[str]:
        """Get Referer header."""
        return self.environ.get('HTTP_REFERER')

    @property
    def origin(self) -> Optional[str]:
        """Get Origin header."""
        return self.environ.get('HTTP_ORIGIN')

    def set_context(self, key: str, value: Any) -> None:
        """Set request-scoped context data."""
        self._context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """Get request-scoped context data."""
        return self._context.get(key, default)

    def has_context(self, key: str) -> bool:
        """Check if context key exists."""
        return key in self._context
