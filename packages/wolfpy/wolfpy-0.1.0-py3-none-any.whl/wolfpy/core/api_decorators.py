"""
WolfPy API Route Decorators.

This module provides simple, convenient decorators for creating REST API endpoints
with automatic JSON handling, validation, and standardized responses.
"""

import json
import inspect
from typing import Dict, List, Any, Optional, Callable, Union
from functools import wraps

from .response import Response
from .request import Request


def api_route(path: str, methods: List[str] = None, status_code: int = 200, 
              validate_json: bool = True, require_auth: bool = False):
    """
    Simple API route decorator with automatic JSON handling.
    
    Args:
        path: URL path pattern
        methods: HTTP methods (default: ['GET'])
        status_code: Default success status code
        validate_json: Whether to validate JSON for POST/PUT/PATCH requests
        require_auth: Whether authentication is required
    
    Returns:
        Decorator function
    """
    if methods is None:
        methods = ['GET']
    
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(request: Request, **kwargs):
            try:
                # Authentication check
                if require_auth:
                    # Basic auth check - can be extended
                    auth_header = request.headers.get('Authorization')
                    if not auth_header:
                        return Response.api_error("Authentication required", 401, "AUTH_REQUIRED")
                
                # JSON validation for data methods
                if request.method in ['POST', 'PUT', 'PATCH'] and validate_json:
                    if not request.is_json():
                        return Response.api_error("Content-Type must be application/json", 400, "INVALID_CONTENT_TYPE")

                    try:
                        # Try to parse JSON manually to catch errors
                        import json as json_module
                        body = request.data.decode(request.charset)
                        if not body.strip():
                            if request.method in ['POST', 'PUT']:
                                return Response.api_error("Request body cannot be empty", 400, "EMPTY_BODY")
                            json_data = None
                        else:
                            json_data = json_module.loads(body)

                        # Add parsed JSON to request for easy access
                        request.api_data = json_data
                    except json_module.JSONDecodeError as e:
                        return Response.api_error(f"Invalid JSON: {str(e)}", 400, "INVALID_JSON")
                    except Exception as e:
                        return Response.api_error(f"Error parsing request: {str(e)}", 400, "PARSE_ERROR")
                
                # Call the original function
                result = func(request, **kwargs)
                
                # Handle different return types
                if isinstance(result, Response):
                    return result
                elif isinstance(result, dict):
                    return Response.json(result, status=status_code)
                elif isinstance(result, (list, tuple)):
                    return Response.json(result, status=status_code)
                elif result is None:
                    return Response.no_content()
                else:
                    return Response.api_success(result, status=status_code)
                    
            except Exception as e:
                return Response.api_error(f"Internal server error: {str(e)}", 500, "INTERNAL_ERROR")
        
        # Store metadata for route registration
        wrapper._api_route_path = path
        wrapper._api_route_methods = methods
        wrapper._api_route_metadata = {
            'path': path,
            'methods': methods,
            'status_code': status_code,
            'validate_json': validate_json,
            'require_auth': require_auth
        }
        
        return wrapper
    
    return decorator


def get_route(path: str, status_code: int = 200):
    """Decorator for GET API routes."""
    return api_route(path, ['GET'], status_code, validate_json=False)


def post_route(path: str, status_code: int = 201, validate_json: bool = True):
    """Decorator for POST API routes."""
    return api_route(path, ['POST'], status_code, validate_json)


def put_route(path: str, status_code: int = 200, validate_json: bool = True):
    """Decorator for PUT API routes."""
    return api_route(path, ['PUT'], status_code, validate_json)


def patch_route(path: str, status_code: int = 200, validate_json: bool = True):
    """Decorator for PATCH API routes."""
    return api_route(path, ['PATCH'], status_code, validate_json)


def delete_route(path: str, status_code: int = 204):
    """Decorator for DELETE API routes."""
    return api_route(path, ['DELETE'], status_code, validate_json=False)


class APIRouter:
    """
    Simple API router that automatically registers decorated routes.
    """
    
    def __init__(self, app, prefix: str = "/api"):
        """
        Initialize API router.
        
        Args:
            app: WolfPy application instance
            prefix: API URL prefix
        """
        self.app = app
        self.prefix = prefix.rstrip('/')
        self.routes = []
    
    def register_routes(self, module_or_class):
        """
        Register all API routes from a module or class.
        
        Args:
            module_or_class: Module or class containing API route functions
        """
        if inspect.ismodule(module_or_class):
            # Register routes from module
            for name in dir(module_or_class):
                obj = getattr(module_or_class, name)
                if callable(obj) and hasattr(obj, '_api_route_metadata'):
                    self._register_route(obj)
        
        elif inspect.isclass(module_or_class):
            # Register routes from class methods
            for name in dir(module_or_class):
                if not name.startswith('_'):
                    method = getattr(module_or_class, name)
                    if callable(method) and hasattr(method, '_api_route_metadata'):
                        self._register_route(method)
        
        else:
            # Single function
            if hasattr(module_or_class, '_api_route_metadata'):
                self._register_route(module_or_class)
    
    def _register_route(self, func: Callable):
        """Register a single API route function."""
        metadata = func._api_route_metadata
        full_path = f"{self.prefix}{metadata['path']}"
        
        # Register with the app
        self.app.route(full_path, methods=metadata['methods'])(func)
        
        # Store route info
        route_info = {
            'path': full_path,
            'methods': metadata['methods'],
            'function': func.__name__,
            'metadata': metadata
        }
        self.routes.append(route_info)
    
    def get_routes(self) -> List[Dict[str, Any]]:
        """Get all registered API routes."""
        return self.routes.copy()


def json_response(data: Any = None, message: str = "Success", status: int = 200,
                 meta: Dict[str, Any] = None):
    """
    Helper function to create standardized JSON responses.

    Args:
        data: Response data
        message: Response message
        status: HTTP status code
        meta: Additional metadata

    Returns:
        Response object
    """
    if status >= 400:
        return Response.api_error(message, status, details=meta)
    else:
        response = Response.api_success(data, message, meta)
        response.status = status  # Override the status code
        return response


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Optional[Response]:
    """
    Validate that required fields are present in data.
    
    Args:
        data: Data dictionary to validate
        required_fields: List of required field names
    
    Returns:
        Error response if validation fails, None if validation passes
    """
    if not isinstance(data, dict):
        return Response.api_error("Request data must be a JSON object", 400, "INVALID_DATA_TYPE")
    
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)
    
    if missing_fields:
        return Response.api_error(
            f"Missing required fields: {', '.join(missing_fields)}", 
            400, 
            "MISSING_FIELDS",
            {'missing_fields': missing_fields}
        )
    
    return None


def paginate_data(data: List[Any], page: int = 1, per_page: int = 10) -> Response:
    """
    Helper function to paginate data and return standardized response.
    
    Args:
        data: List of data to paginate
        page: Page number (1-based)
        per_page: Items per page
    
    Returns:
        Paginated response
    """
    total = len(data)
    start = (page - 1) * per_page
    end = start + per_page
    
    paginated_data = data[start:end]
    has_next = end < total
    has_prev = page > 1
    
    return Response.paginated_response(
        data=paginated_data,
        page=page,
        per_page=per_page,
        total=total,
        has_next=has_next,
        has_prev=has_prev
    )


class EnterpriseAPIFeatures:
    """Enterprise-grade API features for Phase 6 improvements."""

    def __init__(self):
        """Initialize enterprise API features."""
        from collections import defaultdict
        import time

        self.api_versioning = {}
        self.rate_limiting = {}
        self.api_analytics = {
            'endpoint_usage': defaultdict(int),
            'response_times': defaultdict(list),
            'error_rates': defaultdict(int),
            'user_activity': defaultdict(int)
        }
        self.webhook_subscriptions = defaultdict(list)
        self.api_documentation = {}

    def version_api(self, version: str, routes: Dict[str, Callable]):
        """Version API endpoints for backward compatibility."""
        self.api_versioning[version] = routes

    def setup_webhook(self, event: str, callback_url: str, secret: str = None):
        """Setup webhook for API events."""
        import time
        webhook = {
            'url': callback_url,
            'secret': secret,
            'created_at': time.time()
        }
        self.webhook_subscriptions[event].append(webhook)

    def trigger_webhook(self, event: str, data: Dict[str, Any]):
        """Trigger webhook for an event."""
        try:
            import requests
            import hmac
            import hashlib
            import time

            for webhook in self.webhook_subscriptions.get(event, []):
                try:
                    payload = json.dumps(data)
                    headers = {'Content-Type': 'application/json'}

                    # Add signature if secret is provided
                    if webhook['secret']:
                        signature = hmac.new(
                            webhook['secret'].encode(),
                            payload.encode(),
                            hashlib.sha256
                        ).hexdigest()
                        headers['X-Webhook-Signature'] = f"sha256={signature}"

                    # Send webhook (in production, use async/queue)
                    requests.post(webhook['url'], data=payload, headers=headers, timeout=10)

                except Exception as e:
                    print(f"Webhook delivery failed: {e}")
        except ImportError:
            print("Requests library not available for webhook delivery")


def enterprise_api_route(path: str, methods: List[str] = None,
                        version: str = "v1", rate_limit: int = None,
                        cache_ttl: int = None, webhook_events: List[str] = None):
    """Enterprise API route decorator with advanced features."""
    if methods is None:
        methods = ['GET']

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(request: Request, **kwargs):
            import time
            start_time = time.time()

            try:
                # API versioning
                api_version = request.headers.get('API-Version', version)

                # Rate limiting (simplified)
                if rate_limit:
                    client_id = request.headers.get('Authorization', request.remote_addr)
                    # Implement rate limiting logic here

                # Execute original function
                result = func(request, **kwargs)

                # Record analytics
                enterprise_features.api_analytics['endpoint_usage'][path] += 1
                execution_time = time.time() - start_time
                enterprise_features.api_analytics['response_times'][path].append(execution_time)

                # Trigger webhooks if configured
                if webhook_events:
                    for event in webhook_events:
                        enterprise_features.trigger_webhook(event, {
                            'endpoint': path,
                            'method': request.method,
                            'timestamp': time.time(),
                            'execution_time': execution_time
                        })

                # Handle caching
                if cache_ttl and isinstance(result, Response):
                    result.headers['Cache-Control'] = f'max-age={cache_ttl}'

                return result

            except Exception as e:
                # Record error
                enterprise_features.api_analytics['error_rates'][path] += 1
                raise

        # Store metadata
        wrapper._enterprise_api_metadata = {
            'path': path,
            'methods': methods,
            'version': version,
            'rate_limit': rate_limit,
            'cache_ttl': cache_ttl,
            'webhook_events': webhook_events or []
        }

        return wrapper

    return decorator


# Global instances
enterprise_features = EnterpriseAPIFeatures()
