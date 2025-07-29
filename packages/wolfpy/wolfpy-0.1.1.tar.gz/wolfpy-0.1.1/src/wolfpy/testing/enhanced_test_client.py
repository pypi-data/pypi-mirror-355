"""
Enhanced Testing Framework for WolfPy.

This module provides comprehensive testing utilities including:
- Enhanced test client with better assertions
- Mock utilities for testing
- Performance testing tools
- Database testing helpers
- API testing utilities
"""

import json
import time
import threading
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from unittest.mock import Mock, patch
import tempfile
import os
from io import BytesIO, StringIO
import contextlib


@dataclass
class TestResponse:
    """Enhanced test response object."""
    status_code: int
    headers: Dict[str, str]
    body: Union[str, bytes]
    json_data: Optional[Dict[str, Any]] = None
    cookies: Dict[str, str] = field(default_factory=dict)
    execution_time: float = 0.0
    
    def __post_init__(self):
        """Parse JSON data if content type is JSON."""
        content_type = self.headers.get('Content-Type', '')
        if 'application/json' in content_type and isinstance(self.body, (str, bytes)):
            try:
                body_str = self.body.decode('utf-8') if isinstance(self.body, bytes) else self.body
                self.json_data = json.loads(body_str)
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
    
    def assert_status(self, expected_status: int):
        """Assert response status code."""
        assert self.status_code == expected_status, \
            f"Expected status {expected_status}, got {self.status_code}"
    
    def assert_json(self, expected_data: Dict[str, Any] = None, **kwargs):
        """Assert JSON response data."""
        assert self.json_data is not None, "Response is not JSON"
        
        if expected_data:
            assert self.json_data == expected_data, \
                f"JSON mismatch: expected {expected_data}, got {self.json_data}"
        
        for key, value in kwargs.items():
            assert key in self.json_data, f"Key '{key}' not found in JSON response"
            assert self.json_data[key] == value, \
                f"Expected {key}={value}, got {self.json_data[key]}"
    
    def assert_contains(self, text: str):
        """Assert response body contains text."""
        body_str = self.body.decode('utf-8') if isinstance(self.body, bytes) else self.body
        assert text in body_str, f"Response does not contain '{text}'"
    
    def assert_header(self, header_name: str, expected_value: str = None):
        """Assert response header."""
        assert header_name in self.headers, f"Header '{header_name}' not found"
        
        if expected_value:
            actual_value = self.headers[header_name]
            assert actual_value == expected_value, \
                f"Expected header {header_name}={expected_value}, got {actual_value}"
    
    def assert_cookie(self, cookie_name: str, expected_value: str = None):
        """Assert response cookie."""
        assert cookie_name in self.cookies, f"Cookie '{cookie_name}' not found"
        
        if expected_value:
            actual_value = self.cookies[cookie_name]
            assert actual_value == expected_value, \
                f"Expected cookie {cookie_name}={expected_value}, got {actual_value}"
    
    def assert_performance(self, max_time: float):
        """Assert response time is within limit."""
        assert self.execution_time <= max_time, \
            f"Response took {self.execution_time:.3f}s, expected <= {max_time}s"


class EnhancedTestClient:
    """Enhanced test client for WolfPy applications."""
    
    def __init__(self, app):
        """Initialize test client."""
        self.app = app
        self.session_cookies = {}
        self.default_headers = {}
        self.base_url = "http://testserver"
    
    def request(self, method: str, path: str, data: Any = None, json_data: Dict[str, Any] = None,
                headers: Dict[str, str] = None, cookies: Dict[str, str] = None,
                files: Dict[str, Any] = None, follow_redirects: bool = False) -> TestResponse:
        """Make a test request."""
        start_time = time.time()
        
        # Prepare headers
        request_headers = self.default_headers.copy()
        if headers:
            request_headers.update(headers)
        
        # Prepare cookies
        request_cookies = self.session_cookies.copy()
        if cookies:
            request_cookies.update(cookies)
        
        # Prepare body
        body = b''
        if json_data:
            body = json.dumps(json_data).encode('utf-8')
            request_headers['Content-Type'] = 'application/json'
        elif data:
            if isinstance(data, str):
                body = data.encode('utf-8')
            elif isinstance(data, bytes):
                body = data
            elif isinstance(data, dict):
                # Form data
                body = '&'.join(f"{k}={v}" for k, v in data.items()).encode('utf-8')
                request_headers['Content-Type'] = 'application/x-www-form-urlencoded'
        
        # Create WSGI environ
        environ = self._create_environ(method, path, body, request_headers, request_cookies)
        
        # Make request
        response_data = []
        response_status = [200]
        response_headers = {}
        
        def start_response(status, headers):
            response_status[0] = int(status.split()[0])
            for header_name, header_value in headers:
                response_headers[header_name] = header_value
        
        try:
            response_iter = self.app(environ, start_response)
            for chunk in response_iter:
                response_data.append(chunk)
        finally:
            if hasattr(response_iter, 'close'):
                response_iter.close()
        
        # Combine response data
        response_body = b''.join(response_data)
        execution_time = time.time() - start_time
        
        # Parse cookies from response
        response_cookies = {}
        set_cookie_header = response_headers.get('Set-Cookie')
        if set_cookie_header:
            # Simple cookie parsing (for testing purposes)
            for cookie_part in set_cookie_header.split(';'):
                if '=' in cookie_part:
                    name, value = cookie_part.split('=', 1)
                    response_cookies[name.strip()] = value.strip()
        
        # Update session cookies
        self.session_cookies.update(response_cookies)
        
        return TestResponse(
            status_code=response_status[0],
            headers=response_headers,
            body=response_body,
            cookies=response_cookies,
            execution_time=execution_time
        )
    
    def get(self, path: str, **kwargs) -> TestResponse:
        """Make GET request."""
        return self.request('GET', path, **kwargs)
    
    def post(self, path: str, **kwargs) -> TestResponse:
        """Make POST request."""
        return self.request('POST', path, **kwargs)
    
    def put(self, path: str, **kwargs) -> TestResponse:
        """Make PUT request."""
        return self.request('PUT', path, **kwargs)
    
    def patch(self, path: str, **kwargs) -> TestResponse:
        """Make PATCH request."""
        return self.request('PATCH', path, **kwargs)
    
    def delete(self, path: str, **kwargs) -> TestResponse:
        """Make DELETE request."""
        return self.request('DELETE', path, **kwargs)
    
    def set_header(self, name: str, value: str):
        """Set default header for all requests."""
        self.default_headers[name] = value
    
    def set_cookie(self, name: str, value: str):
        """Set session cookie."""
        self.session_cookies[name] = value
    
    def clear_cookies(self):
        """Clear all session cookies."""
        self.session_cookies.clear()
    
    def _create_environ(self, method: str, path: str, body: bytes,
                       headers: Dict[str, str], cookies: Dict[str, str]) -> Dict[str, Any]:
        """Create WSGI environ for testing."""
        if '?' in path:
            path_info, query_string = path.split('?', 1)
        else:
            path_info, query_string = path, ''
        
        environ = {
            'REQUEST_METHOD': method,
            'PATH_INFO': path_info,
            'QUERY_STRING': query_string,
            'CONTENT_TYPE': headers.get('Content-Type', ''),
            'CONTENT_LENGTH': str(len(body)),
            'SERVER_NAME': 'testserver',
            'SERVER_PORT': '80',
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'http',
            'wsgi.input': BytesIO(body),
            'wsgi.errors': StringIO(),
            'wsgi.multithread': False,
            'wsgi.multiprocess': True,
            'wsgi.run_once': False,
        }
        
        # Add headers to environ
        for name, value in headers.items():
            key = f"HTTP_{name.upper().replace('-', '_')}"
            environ[key] = value
        
        # Add cookies
        if cookies:
            cookie_header = '; '.join(f"{name}={value}" for name, value in cookies.items())
            environ['HTTP_COOKIE'] = cookie_header
        
        return environ


class MockDatabase:
    """Mock database for testing."""
    
    def __init__(self):
        """Initialize mock database."""
        self.tables = {}
        self.queries = []
        self.transaction_active = False
    
    def create_table(self, table_name: str, schema: Dict[str, str]):
        """Create a mock table."""
        self.tables[table_name] = {
            'schema': schema,
            'data': [],
            'auto_increment': 1
        }
    
    def insert(self, table_name: str, data: Dict[str, Any]) -> int:
        """Insert data into mock table."""
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} does not exist")
        
        table = self.tables[table_name]
        record = data.copy()
        
        # Add auto-increment ID if not provided
        if 'id' not in record:
            record['id'] = table['auto_increment']
            table['auto_increment'] += 1
        
        table['data'].append(record)
        self.queries.append(f"INSERT INTO {table_name}")
        
        return record['id']
    
    def select(self, table_name: str, where: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Select data from mock table."""
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} does not exist")
        
        data = self.tables[table_name]['data']
        self.queries.append(f"SELECT FROM {table_name}")
        
        if not where:
            return data.copy()
        
        # Simple filtering
        result = []
        for record in data:
            match = True
            for key, value in where.items():
                if record.get(key) != value:
                    match = False
                    break
            if match:
                result.append(record.copy())
        
        return result
    
    def update(self, table_name: str, data: Dict[str, Any], where: Dict[str, Any]) -> int:
        """Update data in mock table."""
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} does not exist")
        
        table_data = self.tables[table_name]['data']
        updated_count = 0
        
        for record in table_data:
            match = True
            for key, value in where.items():
                if record.get(key) != value:
                    match = False
                    break
            
            if match:
                record.update(data)
                updated_count += 1
        
        self.queries.append(f"UPDATE {table_name}")
        return updated_count
    
    def delete(self, table_name: str, where: Dict[str, Any]) -> int:
        """Delete data from mock table."""
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} does not exist")
        
        table_data = self.tables[table_name]['data']
        original_count = len(table_data)
        
        # Filter out matching records
        self.tables[table_name]['data'] = [
            record for record in table_data
            if not all(record.get(k) == v for k, v in where.items())
        ]
        
        deleted_count = original_count - len(self.tables[table_name]['data'])
        self.queries.append(f"DELETE FROM {table_name}")
        
        return deleted_count
    
    def get_queries(self) -> List[str]:
        """Get list of executed queries."""
        return self.queries.copy()
    
    def clear_queries(self):
        """Clear query history."""
        self.queries.clear()
    
    def reset(self):
        """Reset all data."""
        self.tables.clear()
        self.queries.clear()
        self.transaction_active = False


class PerformanceTestRunner:
    """Performance testing utilities."""
    
    def __init__(self, test_client: EnhancedTestClient):
        """Initialize performance test runner."""
        self.client = test_client
        self.results = []
    
    def run_load_test(self, method: str, path: str, num_requests: int = 100,
                     concurrent_users: int = 10, **request_kwargs) -> Dict[str, Any]:
        """Run load test on endpoint."""
        results = []
        threads = []
        
        def make_requests(num_requests_per_thread: int):
            thread_results = []
            for _ in range(num_requests_per_thread):
                start_time = time.time()
                try:
                    response = self.client.request(method, path, **request_kwargs)
                    thread_results.append({
                        'status_code': response.status_code,
                        'response_time': time.time() - start_time,
                        'success': response.status_code < 400
                    })
                except Exception as e:
                    thread_results.append({
                        'status_code': 500,
                        'response_time': time.time() - start_time,
                        'success': False,
                        'error': str(e)
                    })
            results.extend(thread_results)
        
        # Calculate requests per thread
        requests_per_thread = num_requests // concurrent_users
        remaining_requests = num_requests % concurrent_users
        
        # Start threads
        for i in range(concurrent_users):
            thread_requests = requests_per_thread + (1 if i < remaining_requests else 0)
            thread = threading.Thread(target=make_requests, args=(thread_requests,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Calculate statistics
        response_times = [r['response_time'] for r in results]
        success_count = sum(1 for r in results if r['success'])
        
        return {
            'total_requests': len(results),
            'successful_requests': success_count,
            'failed_requests': len(results) - success_count,
            'success_rate': success_count / len(results) * 100,
            'avg_response_time': sum(response_times) / len(response_times),
            'min_response_time': min(response_times),
            'max_response_time': max(response_times),
            'requests_per_second': len(results) / max(response_times) if response_times else 0
        }


@contextlib.contextmanager
def temporary_database():
    """Context manager for temporary test database."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, 'test.db')
    
    try:
        yield db_path
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)
        os.rmdir(temp_dir)


def create_test_app():
    """Create a test WolfPy application."""
    from ..app import WolfPy
    
    app = WolfPy(debug=True)
    
    @app.route('/')
    def home(request):
        return "Hello, Test!"
    
    @app.route('/json')
    def json_endpoint(request):
        from ..response import Response
        return Response.json({'message': 'Hello, JSON!'})
    
    @app.route('/error')
    def error_endpoint(request):
        raise Exception("Test error")
    
    return app
