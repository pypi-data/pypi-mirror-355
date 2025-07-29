"""
WolfPy Response Module.

This module provides enhanced HTTP response generation functionality with
improved performance, security, and developer experience.
"""

import json
import mimetypes
import time
import gzip
import hashlib
from typing import Dict, Any, Union, Optional, List, Iterator, Callable
from datetime import datetime, timedelta
from io import BytesIO


class Response:
    """
    Enhanced HTTP Response object for WolfPy applications.

    Handles response generation including:
    - Status codes and headers
    - Content types and encoding
    - Cookies and redirects
    - JSON and file responses
    - Compression and caching
    - Security headers
    """
    
    # HTTP status codes and their descriptions
    STATUS_CODES = {
        200: 'OK',
        201: 'Created',
        204: 'No Content',
        301: 'Moved Permanently',
        302: 'Found',
        304: 'Not Modified',
        400: 'Bad Request',
        401: 'Unauthorized',
        403: 'Forbidden',
        404: 'Not Found',
        405: 'Method Not Allowed',
        500: 'Internal Server Error',
        502: 'Bad Gateway',
        503: 'Service Unavailable',
    }
    
    def __init__(self,
                 body: Union[str, bytes] = '',
                 status: int = 200,
                 headers: Optional[Dict[str, str]] = None,
                 content_type: str = 'text/html; charset=utf-8',
                 compress: bool = False,
                 cache_control: Optional[str] = None):
        """
        Initialize a response.

        Args:
            body: Response body content
            status: HTTP status code
            headers: Additional headers
            content_type: Content-Type header value
            compress: Whether to compress response body
            cache_control: Cache-Control header value
        """
        self.body = body
        self.status = status
        self.headers = headers or {}
        self.compress = compress
        self._original_body = body

        # Set default content type if not provided in headers
        if 'Content-Type' not in self.headers:
            self.headers['Content-Type'] = content_type

        # Set cache control if provided
        if cache_control:
            self.headers['Cache-Control'] = cache_control

        # Add security headers by default
        self._add_security_headers()

        # Compress body if requested
        if compress and body:
            self._compress_body()
    
    def _add_security_headers(self):
        """Add default security headers."""
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }

        for header, value in security_headers.items():
            if header not in self.headers:
                self.headers[header] = value

    def _compress_body(self):
        """Compress response body using gzip."""
        if isinstance(self.body, str):
            body_bytes = self.body.encode('utf-8')
        else:
            body_bytes = self.body

        if len(body_bytes) > 1024:  # Only compress if body is larger than 1KB
            compressed = gzip.compress(body_bytes)
            if len(compressed) < len(body_bytes):  # Only use if actually smaller
                self.body = compressed
                self.headers['Content-Encoding'] = 'gzip'
                self.headers['Content-Length'] = str(len(compressed))

    @property
    def status_code(self) -> int:
        """Get the status code (alias for status)."""
        return self.status

    @property
    def status_text(self) -> str:
        """Get the status text for the current status code."""
        return self.STATUS_CODES.get(self.status, 'Unknown')
    
    def set_header(self, name: str, value: str):
        """Set a response header."""
        self.headers[name] = value
    
    def add_header(self, name: str, value: str):
        """Add a response header (allows multiple values)."""
        if name in self.headers:
            # Convert to list if not already
            if not isinstance(self.headers[name], list):
                self.headers[name] = [self.headers[name]]
            self.headers[name].append(value)
        else:
            self.headers[name] = value
    
    def set_cookie(self, 
                   name: str, 
                   value: str,
                   max_age: Optional[int] = None,
                   expires: Optional[datetime] = None,
                   path: str = '/',
                   domain: Optional[str] = None,
                   secure: bool = False,
                   httponly: bool = False,
                   samesite: Optional[str] = None):
        """
        Set a cookie in the response.
        
        Args:
            name: Cookie name
            value: Cookie value
            max_age: Cookie max age in seconds
            expires: Cookie expiration datetime
            path: Cookie path
            domain: Cookie domain
            secure: Secure flag
            httponly: HttpOnly flag
            samesite: SameSite attribute ('Strict', 'Lax', or 'None')
        """
        cookie_parts = [f"{name}={value}"]
        
        if max_age is not None:
            cookie_parts.append(f"Max-Age={max_age}")
        
        if expires is not None:
            expires_str = expires.strftime('%a, %d %b %Y %H:%M:%S GMT')
            cookie_parts.append(f"Expires={expires_str}")
        
        if path:
            cookie_parts.append(f"Path={path}")
        
        if domain:
            cookie_parts.append(f"Domain={domain}")
        
        if secure:
            cookie_parts.append("Secure")
        
        if httponly:
            cookie_parts.append("HttpOnly")
        
        if samesite:
            cookie_parts.append(f"SameSite={samesite}")
        
        cookie_header = '; '.join(cookie_parts)
        self.add_header('Set-Cookie', cookie_header)
    
    def delete_cookie(self, name: str, path: str = '/', domain: Optional[str] = None):
        """
        Delete a cookie by setting it to expire in the past.

        Args:
            name: Cookie name
            path: Cookie path
            domain: Cookie domain
        """
        expires = datetime.utcnow() - timedelta(days=1)
        self.set_cookie(name, '', expires=expires, path=path, domain=domain)

    def set_etag(self, etag: str, weak: bool = False):
        """
        Set ETag header for caching.

        Args:
            etag: ETag value
            weak: Whether this is a weak ETag
        """
        if weak:
            self.headers['ETag'] = f'W/"{etag}"'
        else:
            self.headers['ETag'] = f'"{etag}"'

    def generate_etag(self, include_last_modified: bool = True):
        """
        Generate ETag based on response content.

        Args:
            include_last_modified: Whether to include Last-Modified in ETag calculation
        """
        content = self._original_body if hasattr(self, '_original_body') else self.body
        if isinstance(content, str):
            content = content.encode('utf-8')

        etag_data = content
        if include_last_modified and 'Last-Modified' in self.headers:
            etag_data += self.headers['Last-Modified'].encode('utf-8')

        etag = hashlib.md5(etag_data).hexdigest()
        self.set_etag(etag)
        return etag

    def set_cache_control(self, **directives):
        """
        Set Cache-Control header with directives.

        Args:
            **directives: Cache control directives (max_age, no_cache, etc.)
        """
        cache_parts = []

        for directive, value in directives.items():
            directive = directive.replace('_', '-')
            if value is True:
                cache_parts.append(directive)
            elif value is not False:
                cache_parts.append(f"{directive}={value}")

        if cache_parts:
            self.headers['Cache-Control'] = ', '.join(cache_parts)

    def set_last_modified(self, timestamp: Union[datetime, float, int]):
        """
        Set Last-Modified header.

        Args:
            timestamp: Timestamp as datetime, float, or int
        """
        if isinstance(timestamp, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp)

        self.headers['Last-Modified'] = timestamp.strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    @classmethod
    def json(cls, data: Any, status: int = 200, headers: Optional[Dict[str, str]] = None,
             indent: Optional[int] = None, ensure_ascii: bool = False,
             compress: bool = False, cache_control: Optional[str] = None):
        """
        Create an enhanced JSON response.

        Args:
            data: Data to serialize as JSON
            status: HTTP status code
            headers: Additional headers
            indent: JSON indentation (None for compact, 2 for pretty)
            ensure_ascii: Whether to escape non-ASCII characters
            compress: Whether to compress response
            cache_control: Cache-Control header value

        Returns:
            Response object with JSON content
        """
        # Handle datetime objects in JSON serialization
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        json_data = json.dumps(data, ensure_ascii=ensure_ascii, indent=indent,
                              default=json_serializer, separators=(',', ':') if indent is None else None)

        response_headers = headers or {}
        response_headers['Content-Type'] = 'application/json; charset=utf-8'

        return cls(json_data, status=status, headers=response_headers,
                  compress=compress, cache_control=cache_control)

    @classmethod
    def html(cls, html_content: str, status: int = 200, headers: Optional[Dict[str, str]] = None):
        """
        Create an HTML response.

        Args:
            html_content: HTML content string
            status: HTTP status code (default: 200)
            headers: Additional headers

        Returns:
            Response object with HTML content
        """
        response_headers = headers.copy() if headers else {}
        response_headers['Content-Type'] = 'text/html; charset=utf-8'

        return cls(html_content, status=status, headers=response_headers)

    @classmethod
    def redirect(cls, location: str, status: int = 302):
        """
        Create a redirect response.
        
        Args:
            location: URL to redirect to
            status: HTTP status code (301 or 302)
            
        Returns:
            Response object with redirect
        """
        headers = {'Location': location}
        return cls('', status=status, headers=headers)
    
    @classmethod
    def file(cls, file_path: str, as_attachment: bool = False, filename: Optional[str] = None):
        """
        Create a file response.
        
        Args:
            file_path: Path to the file
            as_attachment: Whether to serve as download
            filename: Custom filename for download
            
        Returns:
            Response object with file content
        """
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Guess content type
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                content_type = 'application/octet-stream'
            
            headers = {'Content-Type': content_type}
            
            if as_attachment:
                attachment_filename = filename or file_path.split('/')[-1]
                headers['Content-Disposition'] = f'attachment; filename="{attachment_filename}"'
            
            return cls(content, headers=headers)
            
        except FileNotFoundError:
            return cls('File not found', status=404)
        except Exception:
            return cls('Error reading file', status=500)
    
    @classmethod
    def not_found(cls, message: str = 'Not Found'):
        """Create a 404 Not Found response."""
        return cls(message, status=404)
    
    @classmethod
    def bad_request(cls, message: Union[str, Dict[str, Any]] = 'Bad Request'):
        """Create a 400 Bad Request response."""
        if isinstance(message, dict):
            return cls.json(message, status=400)
        return cls(message, status=400)

    @classmethod
    def unauthorized(cls, message: Union[str, Dict[str, Any]] = 'Unauthorized'):
        """Create a 401 Unauthorized response."""
        if isinstance(message, dict):
            return cls.json(message, status=401)
        return cls(message, status=401)

    @classmethod
    def forbidden(cls, message: Union[str, Dict[str, Any]] = 'Forbidden'):
        """Create a 403 Forbidden response."""
        if isinstance(message, dict):
            return cls.json(message, status=403)
        return cls(message, status=403)

    @classmethod
    def internal_error(cls, message: Union[str, Dict[str, Any]] = 'Internal Server Error'):
        """Create a 500 Internal Server Error response."""
        if isinstance(message, dict):
            return cls.json(message, status=500)
        return cls(message, status=500)

    @classmethod
    def server_error(cls, message: Union[str, Dict[str, Any]] = 'Internal Server Error'):
        """Create a 500 Internal Server Error response. Alias for internal_error."""
        return cls.internal_error(message)

    @classmethod
    def method_not_allowed(cls, allowed_methods: List[str], message: str = 'Method Not Allowed'):
        """Create a 405 Method Not Allowed response."""
        headers = {'Allow': ', '.join(allowed_methods)}
        return cls(message, status=405, headers=headers)

    @classmethod
    def no_content(cls):
        """Create a 204 No Content response."""
        return cls('', status=204)

    @classmethod
    def created(cls, data: Any = None, location: str = None):
        """Create a 201 Created response."""
        headers = {}
        if location:
            headers['Location'] = location

        if data is not None:
            if isinstance(data, dict):
                return cls.json(data, status=201, headers=headers)
            else:
                return cls(str(data), status=201, headers=headers)
        else:
            return cls('', status=201, headers=headers)

    # Enhanced JSON response helpers for REST API
    @classmethod
    def accepted(cls, data: Any = None, message: str = "Request accepted for processing"):
        """Create a 202 Accepted response."""
        if data is not None:
            if isinstance(data, dict):
                return cls.json(data, status=202)
            else:
                return cls.json({'message': message, 'data': data}, status=202)
        return cls.json({'message': message}, status=202)

    @classmethod
    def partial_content(cls, data: Any, content_range: str = None):
        """Create a 206 Partial Content response."""
        headers = {}
        if content_range:
            headers['Content-Range'] = content_range

        if isinstance(data, dict):
            return cls.json(data, status=206, headers=headers)
        return cls(str(data), status=206, headers=headers)

    @classmethod
    def not_modified(cls):
        """Create a 304 Not Modified response."""
        return cls('', status=304)

    @classmethod
    def unprocessable_entity(cls, errors: Union[str, Dict[str, Any], List[str]] = None):
        """Create a 422 Unprocessable Entity response."""
        if errors is None:
            errors = "Unprocessable Entity"

        if isinstance(errors, str):
            return cls.json({'error': errors}, status=422)
        elif isinstance(errors, list):
            return cls.json({'errors': errors}, status=422)
        else:
            return cls.json(errors, status=422)

    @classmethod
    def too_many_requests(cls, message: str = "Too Many Requests", retry_after: int = None):
        """Create a 429 Too Many Requests response."""
        headers = {}
        if retry_after:
            headers['Retry-After'] = str(retry_after)

        return cls.json({'error': message}, status=429, headers=headers)

    @classmethod
    def conflict(cls, message: Union[str, Dict[str, Any]] = "Conflict"):
        """Create a 409 Conflict response."""
        if isinstance(message, dict):
            return cls.json(message, status=409)
        return cls.json({'error': message}, status=409)

    @classmethod
    def gone(cls, message: Union[str, Dict[str, Any]] = "Gone"):
        """Create a 410 Gone response."""
        if isinstance(message, dict):
            return cls.json(message, status=410)
        return cls.json({'error': message}, status=410)

    @classmethod
    def service_unavailable(cls, message: str = "Service Unavailable", retry_after: int = None):
        """Create a 503 Service Unavailable response."""
        headers = {}
        if retry_after:
            headers['Retry-After'] = str(retry_after)

        return cls.json({'error': message}, status=503, headers=headers)

    @classmethod
    def bad_gateway(cls, message: Union[str, Dict[str, Any]] = "Bad Gateway"):
        """Create a 502 Bad Gateway response."""
        if isinstance(message, dict):
            return cls.json(message, status=502)
        return cls.json({'error': message}, status=502)

    @classmethod
    def gateway_timeout(cls, message: Union[str, Dict[str, Any]] = "Gateway Timeout"):
        """Create a 504 Gateway Timeout response."""
        if isinstance(message, dict):
            return cls.json(message, status=504)
        return cls.json({'error': message}, status=504)

    # REST API specific response helpers
    @classmethod
    def api_success(cls, data: Any = None, message: str = "Success", meta: Dict[str, Any] = None):
        """Create a standardized API success response."""
        response_data = {
            'success': True,
            'message': message
        }

        if data is not None:
            response_data['data'] = data

        if meta:
            response_data['meta'] = meta

        return cls.json(response_data, status=200)

    @classmethod
    def api_error(cls, message: str, status: int = 400, error_code: str = None, details: Dict[str, Any] = None):
        """Create a standardized API error response."""
        response_data = {
            'success': False,
            'error': {
                'message': message,
                'status': status
            }
        }

        if error_code:
            response_data['error']['code'] = error_code

        if details:
            response_data['error']['details'] = details

        return cls.json(response_data, status=status)

    @classmethod
    def paginated_response(cls, data: List[Any], page: int = 1, per_page: int = 10,
                          total: int = None, has_next: bool = False, has_prev: bool = False):
        """Create a paginated API response."""
        response_data = {
            'success': True,
            'data': data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'has_next': has_next,
                'has_prev': has_prev
            }
        }

        if total is not None:
            response_data['pagination']['total'] = total
            response_data['pagination']['pages'] = (total + per_page - 1) // per_page

        return cls.json(response_data, status=200)

    def is_success(self) -> bool:
        """Check if response status indicates success (2xx)."""
        return 200 <= self.status < 300

    def is_redirect(self) -> bool:
        """Check if response status indicates redirect (3xx)."""
        return 300 <= self.status < 400

    def is_client_error(self) -> bool:
        """Check if response status indicates client error (4xx)."""
        return 400 <= self.status < 500

    def is_server_error(self) -> bool:
        """Check if response status indicates server error (5xx)."""
        return 500 <= self.status < 600

    def __str__(self) -> str:
        """String representation of the response."""
        return f"<Response {self.status} {self.status_text}>"

    def __repr__(self) -> str:
        """Detailed string representation of the response."""
        return f"Response(status={self.status}, headers={self.headers})"


class StreamingResponse(Response):
    """
    Streaming response for large files or real-time data.
    """

    def __init__(self,
                 generator: Union[Iterator[bytes], Callable[[], Iterator[bytes]]],
                 status: int = 200,
                 headers: Optional[Dict[str, str]] = None,
                 content_type: str = 'text/plain; charset=utf-8',
                 chunk_size: int = 8192):
        """
        Initialize streaming response.

        Args:
            generator: Iterator or callable that yields bytes
            status: HTTP status code
            headers: Additional headers
            content_type: Content-Type header value
            chunk_size: Size of chunks to stream
        """
        super().__init__('', status=status, headers=headers, content_type=content_type)
        self.generator = generator
        self.chunk_size = chunk_size
        self.is_streaming = True

    def iter_content(self) -> Iterator[bytes]:
        """
        Iterate over response content.

        Yields:
            Chunks of response data
        """
        if callable(self.generator):
            generator = self.generator()
        else:
            generator = self.generator

        for chunk in generator:
            if isinstance(chunk, str):
                chunk = chunk.encode('utf-8')
            yield chunk

    @classmethod
    def from_file(cls, file_path: str, chunk_size: int = 8192):
        """
        Create streaming response from file.

        Args:
            file_path: Path to file
            chunk_size: Size of chunks to read

        Returns:
            StreamingResponse instance
        """
        def file_generator():
            try:
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        yield chunk
            except FileNotFoundError:
                yield b'File not found'

        # Guess content type
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = 'application/octet-stream'

        return cls(file_generator, content_type=content_type, chunk_size=chunk_size)

    @classmethod
    def from_string_generator(cls, string_generator: Iterator[str],
                            content_type: str = 'text/plain; charset=utf-8'):
        """
        Create streaming response from string generator.

        Args:
            string_generator: Generator that yields strings
            content_type: Content type

        Returns:
            StreamingResponse instance
        """
        def byte_generator():
            for string_chunk in string_generator:
                yield string_chunk.encode('utf-8')

        return cls(byte_generator, content_type=content_type)


class ServerSentEventsResponse(StreamingResponse):
    """
    Server-Sent Events (SSE) response for real-time updates.
    """

    def __init__(self,
                 event_generator: Union[Iterator[Dict[str, Any]], Callable[[], Iterator[Dict[str, Any]]]],
                 status: int = 200,
                 headers: Optional[Dict[str, str]] = None):
        """
        Initialize SSE response.

        Args:
            event_generator: Iterator or callable that yields event dictionaries
            status: HTTP status code
            headers: Additional headers
        """
        sse_headers = {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Cache-Control'
        }

        if headers:
            sse_headers.update(headers)

        def sse_generator():
            if callable(event_generator):
                generator = event_generator()
            else:
                generator = event_generator

            for event in generator:
                yield self._format_sse_event(event)

        super().__init__(sse_generator, status=status, headers=sse_headers)

    def _format_sse_event(self, event: Dict[str, Any]) -> bytes:
        """
        Format event as SSE message.

        Args:
            event: Event dictionary with 'data', 'event', 'id', 'retry' keys

        Returns:
            Formatted SSE message as bytes
        """
        lines = []

        if 'id' in event:
            lines.append(f"id: {event['id']}")

        if 'event' in event:
            lines.append(f"event: {event['event']}")

        if 'retry' in event:
            lines.append(f"retry: {event['retry']}")

        if 'data' in event:
            data = event['data']
            if isinstance(data, dict):
                data = json.dumps(data)
            elif not isinstance(data, str):
                data = str(data)

            # Handle multi-line data
            for line in data.split('\n'):
                lines.append(f"data: {line}")

        lines.append('')  # Empty line to end event
        return '\n'.join(lines).encode('utf-8') + b'\n'

    @classmethod
    def heartbeat(cls, interval: int = 30):
        """
        Create SSE response with periodic heartbeat.

        Args:
            interval: Heartbeat interval in seconds

        Returns:
            ServerSentEventsResponse instance
        """
        def heartbeat_generator():
            while True:
                yield {
                    'event': 'heartbeat',
                    'data': {'timestamp': time.time()}
                }
                time.sleep(interval)

        return cls(heartbeat_generator)


class ChunkedResponse(StreamingResponse):
    """
    Chunked transfer encoding response.
    """

    def __init__(self,
                 generator: Union[Iterator[bytes], Callable[[], Iterator[bytes]]],
                 status: int = 200,
                 headers: Optional[Dict[str, str]] = None,
                 content_type: str = 'text/html; charset=utf-8'):
        """
        Initialize chunked response.

        Args:
            generator: Iterator or callable that yields bytes
            status: HTTP status code
            headers: Additional headers
            content_type: Content-Type header value
        """
        chunked_headers = {'Transfer-Encoding': 'chunked'}
        if headers:
            chunked_headers.update(headers)

        super().__init__(generator, status=status, headers=chunked_headers, content_type=content_type)

    def iter_content(self) -> Iterator[bytes]:
        """
        Iterate over chunked content.

        Yields:
            HTTP chunks with size headers
        """
        for chunk in super().iter_content():
            if chunk:
                # Format as HTTP chunk: size in hex + CRLF + data + CRLF
                chunk_size = hex(len(chunk))[2:].encode('ascii')
                yield chunk_size + b'\r\n' + chunk + b'\r\n'

        # End with zero-size chunk
        yield b'0\r\n\r\n'
