"""
WolfPy Advanced API Framework.

This module provides comprehensive REST API functionality including
automatic documentation, validation, serialization, versioning,
and OpenAPI/Swagger support.
"""

import json
import inspect
import time
import math
from typing import Dict, List, Any, Optional, Callable, Type, Union, get_type_hints, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from enum import Enum
from functools import wraps
from collections import defaultdict
import re

from .response import Response
from .request import Request


class APIError(Exception):
    """Base API error."""
    
    def __init__(self, message: str, status_code: int = 400, details: Dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class ValidationError(APIError):
    """Validation error."""

    def __init__(self, message: str, field: str = None, details: Dict = None):
        self.field = field
        super().__init__(message, 400, details)


class RateLimitError(APIError):
    """Rate limit exceeded error."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        self.retry_after = retry_after
        super().__init__(message, 429)


@dataclass
class PaginationInfo:
    """Pagination information."""
    page: int = 1
    per_page: int = 20
    total_items: int = 0
    total_pages: int = 0
    has_next: bool = False
    has_prev: bool = False
    next_page: Optional[int] = None
    prev_page: Optional[int] = None

    @classmethod
    def from_request(cls, request: Request, default_per_page: int = 20, max_per_page: int = 100) -> 'PaginationInfo':
        """Create pagination info from request parameters."""
        try:
            page = int(request.args.get('page', 1))
            page = max(1, page)  # Ensure page is at least 1
        except (ValueError, TypeError):
            page = 1

        try:
            per_page = int(request.args.get('per_page', default_per_page))
            per_page = min(max(1, per_page), max_per_page)  # Clamp between 1 and max
        except (ValueError, TypeError):
            per_page = default_per_page

        return cls(page=page, per_page=per_page)

    def calculate_pagination(self, total_items: int):
        """Calculate pagination values."""
        self.total_items = total_items
        self.total_pages = math.ceil(total_items / self.per_page) if self.per_page > 0 else 0

        self.has_prev = self.page > 1
        self.has_next = self.page < self.total_pages

        self.prev_page = self.page - 1 if self.has_prev else None
        self.next_page = self.page + 1 if self.has_next else None

    def get_offset(self) -> int:
        """Get SQL offset for this page."""
        return (self.page - 1) * self.per_page

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            'page': self.page,
            'per_page': self.per_page,
            'total_items': self.total_items,
            'total_pages': self.total_pages,
            'has_next': self.has_next,
            'has_prev': self.has_prev,
            'next_page': self.next_page,
            'prev_page': self.prev_page
        }


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)  # client_id -> list of timestamps

    def is_allowed(self, client_id: str) -> Tuple[bool, Optional[int]]:
        """
        Check if request is allowed.

        Args:
            client_id: Client identifier (IP, user ID, etc.)

        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        now = time.time()
        cutoff = now - self.window_seconds

        # Clean old requests
        self.requests[client_id] = [
            timestamp for timestamp in self.requests[client_id]
            if timestamp > cutoff
        ]

        # Check if under limit
        if len(self.requests[client_id]) < self.max_requests:
            self.requests[client_id].append(now)
            return True, None
        else:
            # Calculate retry after
            oldest_request = min(self.requests[client_id])
            retry_after = int(oldest_request + self.window_seconds - now)
            return False, max(1, retry_after)

    def get_remaining(self, client_id: str) -> int:
        """Get remaining requests for client."""
        now = time.time()
        cutoff = now - self.window_seconds

        # Clean old requests
        self.requests[client_id] = [
            timestamp for timestamp in self.requests[client_id]
            if timestamp > cutoff
        ]

        return max(0, self.max_requests - len(self.requests[client_id]))


class APISerializer:
    """Advanced serializer for API responses."""

    def __init__(self, include_fields: List[str] = None, exclude_fields: List[str] = None,
                 nested_serializers: Dict[str, 'APISerializer'] = None):
        """
        Initialize serializer.

        Args:
            include_fields: Fields to include (if None, include all)
            exclude_fields: Fields to exclude
            nested_serializers: Serializers for nested objects
        """
        self.include_fields = include_fields
        self.exclude_fields = exclude_fields or []
        self.nested_serializers = nested_serializers or {}

    def serialize(self, obj: Any) -> Any:
        """Serialize an object."""
        if obj is None:
            return None
        elif isinstance(obj, (list, tuple)):
            return [self.serialize(item) for item in obj]
        elif isinstance(obj, dict):
            return self._serialize_dict(obj)
        elif hasattr(obj, 'to_dict'):
            # Model or dataclass with to_dict method
            return self._serialize_dict(obj.to_dict())
        elif hasattr(obj, '__dict__'):
            # Regular object
            return self._serialize_dict(obj.__dict__)
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, Enum):
            return obj.value
        else:
            return obj

    def _serialize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize a dictionary."""
        result = {}

        for key, value in data.items():
            # Skip private fields
            if key.startswith('_'):
                continue

            # Apply field filtering
            if self.include_fields and key not in self.include_fields:
                continue

            if key in self.exclude_fields:
                continue

            # Use nested serializer if available
            if key in self.nested_serializers:
                result[key] = self.nested_serializers[key].serialize(value)
            else:
                result[key] = self.serialize(value)

        return result


class APIVersionManager:
    """Manages API versioning."""

    def __init__(self):
        """Initialize version manager."""
        self.versions = {}
        self.default_version = None

    def register_version(self, version: str, is_default: bool = False, handler: Callable = None):
        """Register an API version."""
        self.versions[version] = {
            'endpoints': {},
            'deprecated': False,
            'sunset_date': None,
            'handler': handler
        }

        if is_default or not self.default_version:
            self.default_version = version

    def deprecate_version(self, version: str, sunset_date: datetime = None):
        """Mark a version as deprecated."""
        if version in self.versions:
            self.versions[version]['deprecated'] = True
            self.versions[version]['sunset_date'] = sunset_date

    def get_version_from_request(self, request: Request) -> str:
        """Extract API version from request."""
        # Try header first
        version = request.headers.get('API-Version')
        if version and version in self.versions:
            return version

        # Try Accept header
        accept = request.headers.get('Accept', '')
        if 'application/vnd.api+json' in accept:
            # Parse version from Accept header
            for part in accept.split(','):
                if 'version=' in part:
                    version = part.split('version=')[1].strip()
                    if version in self.versions:
                        return version

        # Try URL parameter
        version = request.args.get('version')
        if version and version in self.versions:
            return version

        # Return default
        return self.default_version

    def is_version_deprecated(self, version: str) -> bool:
        """Check if version is deprecated."""
        return self.versions.get(version, {}).get('deprecated', False)


def paginate_data(data: List[Any], pagination: PaginationInfo,
                 serializer: APISerializer = None) -> Dict[str, Any]:
    """
    Paginate data and return API response.

    Args:
        data: List of data to paginate
        pagination: Pagination information
        serializer: Optional serializer for data

    Returns:
        Paginated API response
    """
    # Calculate pagination
    pagination.calculate_pagination(len(data))

    # Get page data
    start = pagination.get_offset()
    end = start + pagination.per_page
    page_data = data[start:end]

    # Serialize if serializer provided
    if serializer:
        page_data = serializer.serialize(page_data)

    return {
        'data': page_data,
        'pagination': pagination.to_dict()
    }


def create_error_response(error: Exception, include_traceback: bool = False) -> Dict[str, Any]:
    """
    Create standardized error response.

    Args:
        error: Exception that occurred
        include_traceback: Whether to include traceback (for debugging)

    Returns:
        Error response dictionary
    """
    if isinstance(error, APIError):
        response = {
            'error': {
                'type': type(error).__name__,
                'message': error.message,
                'status_code': error.status_code
            }
        }

        if error.details:
            response['error']['details'] = error.details

        if isinstance(error, ValidationError) and error.field:
            response['error']['field'] = error.field

        if isinstance(error, RateLimitError) and error.retry_after:
            response['error']['retry_after'] = error.retry_after
    else:
        response = {
            'error': {
                'type': type(error).__name__,
                'message': str(error),
                'status_code': 500
            }
        }

    if include_traceback:
        import traceback
        response['error']['traceback'] = traceback.format_exc()

    return response


@dataclass
class APIField:
    """API field definition."""
    type: Type
    required: bool = True
    default: Any = None
    description: str = ""
    example: Any = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None
    enum_values: Optional[List[Any]] = None

    def __init__(self, field_type: Type, required: bool = True, default: Any = None,
                 description: str = "", example: Any = None, min_length: Optional[int] = None,
                 max_length: Optional[int] = None, min_value: Optional[Union[int, float]] = None,
                 max_value: Optional[Union[int, float]] = None, pattern: Optional[str] = None,
                 enum_values: Optional[List[Any]] = None):
        self.type = field_type
        self.required = required
        self.default = default
        self.description = description
        self.example = example
        self.min_length = min_length
        self.max_length = max_length
        self.min_value = min_value
        self.max_value = max_value
        self.pattern = pattern
        self.enum_values = enum_values


class APIModel:
    """Base API model with validation."""

    def __init__(self, **kwargs):
        """Initialize model with provided data."""
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'APIModel':
        """Create model instance from dictionary."""
        # Get type hints for validation
        type_hints = get_type_hints(cls)
        validated_data = {}
        
        for field_name, field_type in type_hints.items():
            if field_name.startswith('_'):
                continue
            
            value = data.get(field_name)
            
            # Check if field is required
            field_info = getattr(cls, field_name, None)
            if isinstance(field_info, APIField):
                if field_info.required and value is None:
                    raise ValidationError(f"Field '{field_name}' is required")
                
                # Validate field
                validated_value = cls._validate_field(field_name, value, field_info)
                validated_data[field_name] = validated_value
            else:
                validated_data[field_name] = value
        
        return cls(**validated_data)
    
    @classmethod
    def _validate_field(cls, name: str, value: Any, field_info: APIField) -> Any:
        """Validate a single field."""
        if value is None:
            if field_info.required:
                raise ValidationError(f"Field '{name}' is required")
            return field_info.default
        
        # Type validation
        if not isinstance(value, field_info.type):
            try:
                value = field_info.type(value)
            except (ValueError, TypeError):
                raise ValidationError(f"Field '{name}' must be of type {field_info.type.__name__}")
        
        # String validations
        if isinstance(value, str):
            if field_info.min_length and len(value) < field_info.min_length:
                raise ValidationError(f"Field '{name}' must be at least {field_info.min_length} characters")
            
            if field_info.max_length and len(value) > field_info.max_length:
                raise ValidationError(f"Field '{name}' must be at most {field_info.max_length} characters")
            
            if field_info.pattern and not re.match(field_info.pattern, value):
                raise ValidationError(f"Field '{name}' does not match required pattern")
        
        # Numeric validations
        if isinstance(value, (int, float)):
            if field_info.min_value is not None and value < field_info.min_value:
                raise ValidationError(f"Field '{name}' must be at least {field_info.min_value}")
            
            if field_info.max_value is not None and value > field_info.max_value:
                raise ValidationError(f"Field '{name}' must be at most {field_info.max_value}")
        
        # Enum validation
        if field_info.enum_values and value not in field_info.enum_values:
            raise ValidationError(f"Field '{name}' must be one of {field_info.enum_values}")
        
        return value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        result = {}

        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, date):
                result[key] = value.isoformat()
            elif isinstance(value, Enum):
                result[key] = value.value
            else:
                result[key] = value

        return result


class APIEndpoint:
    """API endpoint definition."""
    
    def __init__(self, path: str, method: str, handler: Callable,
                 summary: str = "", description: str = "",
                 request_model: Type[APIModel] = None,
                 response_model: Type[APIModel] = None,
                 tags: List[str] = None,
                 deprecated: bool = False):
        """
        Initialize API endpoint.
        
        Args:
            path: URL path
            method: HTTP method
            handler: Handler function
            summary: Short description
            description: Detailed description
            request_model: Request body model
            response_model: Response model
            tags: Endpoint tags for grouping
            deprecated: Whether endpoint is deprecated
        """
        self.path = path
        self.method = method.upper()
        self.handler = handler
        self.summary = summary
        self.description = description
        self.request_model = request_model
        self.response_model = response_model
        self.tags = tags or []
        self.deprecated = deprecated
        
        # Extract info from handler
        self._extract_handler_info()
    
    def _extract_handler_info(self):
        """Extract information from handler function."""
        if not self.summary and self.handler.__doc__:
            lines = self.handler.__doc__.strip().split('\n')
            self.summary = lines[0].strip()
            if len(lines) > 1:
                self.description = '\n'.join(lines[1:]).strip()
        
        # Extract type hints
        type_hints = get_type_hints(self.handler)
        
        # Try to infer request/response models from type hints
        if 'request' in type_hints and not self.request_model:
            request_type = type_hints['request']
            if hasattr(request_type, '__origin__') and request_type.__origin__ is Union:
                # Handle Optional types
                args = request_type.__args__
                for arg in args:
                    if arg != type(None) and issubclass(arg, APIModel):
                        self.request_model = arg
                        break
            elif inspect.isclass(request_type) and issubclass(request_type, APIModel):
                self.request_model = request_type
        
        if 'return' in type_hints and not self.response_model:
            return_type = type_hints['return']
            if inspect.isclass(return_type) and issubclass(return_type, APIModel):
                self.response_model = return_type


class APIDocumentation:
    """API documentation generator."""
    
    def __init__(self, title: str = "API", version: str = "1.0.0",
                 description: str = ""):
        """
        Initialize API documentation.
        
        Args:
            title: API title
            version: API version
            description: API description
        """
        self.title = title
        self.version = version
        self.description = description
        self.endpoints = []
        self.models = {}
    
    def add_endpoint(self, endpoint: APIEndpoint):
        """Add endpoint to documentation."""
        self.endpoints.append(endpoint)
        
        # Register models
        if endpoint.request_model:
            self.models[endpoint.request_model.__name__] = endpoint.request_model
        
        if endpoint.response_model:
            self.models[endpoint.response_model.__name__] = endpoint.response_model
    
    def generate_openapi_spec(self) -> Dict[str, Any]:
        """Generate OpenAPI 3.0 specification."""
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": self.title,
                "version": self.version,
                "description": self.description
            },
            "paths": {},
            "components": {
                "schemas": {}
            }
        }
        
        # Add endpoints
        for endpoint in self.endpoints:
            path = endpoint.path
            method = endpoint.method.lower()
            
            if path not in spec["paths"]:
                spec["paths"][path] = {}
            
            operation = {
                "summary": endpoint.summary,
                "description": endpoint.description,
                "tags": endpoint.tags,
                "deprecated": endpoint.deprecated
            }
            
            # Add request body
            if endpoint.request_model:
                operation["requestBody"] = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": f"#/components/schemas/{endpoint.request_model.__name__}"
                            }
                        }
                    }
                }
            
            # Add responses
            operation["responses"] = {
                "200": {
                    "description": "Success"
                }
            }
            
            if endpoint.response_model:
                operation["responses"]["200"]["content"] = {
                    "application/json": {
                        "schema": {
                            "$ref": f"#/components/schemas/{endpoint.response_model.__name__}"
                        }
                    }
                }
            
            spec["paths"][path][method] = operation
        
        # Add model schemas
        for model_name, model_class in self.models.items():
            spec["components"]["schemas"][model_name] = self._generate_model_schema(model_class)
        
        return spec
    
    def _generate_model_schema(self, model_class: Type[APIModel]) -> Dict[str, Any]:
        """Generate JSON schema for a model."""
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        type_hints = get_type_hints(model_class)
        
        for field_name, field_type in type_hints.items():
            if field_name.startswith('_'):
                continue
            
            field_info = getattr(model_class, field_name, None)
            
            property_schema = self._type_to_schema(field_type)
            
            if isinstance(field_info, APIField):
                if field_info.description:
                    property_schema["description"] = field_info.description
                
                if field_info.example is not None:
                    property_schema["example"] = field_info.example
                
                if field_info.required:
                    schema["required"].append(field_name)
                
                # Add validation constraints
                if field_info.min_length is not None:
                    property_schema["minLength"] = field_info.min_length
                
                if field_info.max_length is not None:
                    property_schema["maxLength"] = field_info.max_length
                
                if field_info.min_value is not None:
                    property_schema["minimum"] = field_info.min_value
                
                if field_info.max_value is not None:
                    property_schema["maximum"] = field_info.max_value
                
                if field_info.pattern:
                    property_schema["pattern"] = field_info.pattern
                
                if field_info.enum_values:
                    property_schema["enum"] = field_info.enum_values
            
            schema["properties"][field_name] = property_schema
        
        return schema
    
    def _type_to_schema(self, type_hint: Type) -> Dict[str, Any]:
        """Convert Python type to JSON schema type."""
        if type_hint == str:
            return {"type": "string"}
        elif type_hint == int:
            return {"type": "integer"}
        elif type_hint == float:
            return {"type": "number"}
        elif type_hint == bool:
            return {"type": "boolean"}
        elif type_hint == list:
            return {"type": "array"}
        elif type_hint == dict:
            return {"type": "object"}
        elif type_hint == datetime:
            return {"type": "string", "format": "date-time"}
        elif type_hint == date:
            return {"type": "string", "format": "date"}
        else:
            return {"type": "object"}


class APIFramework:
    """Advanced API framework for WolfPy."""

    def __init__(self, app, prefix: str = "/api", version: str = "v1",
                 enable_rate_limiting: bool = True, enable_versioning: bool = True,
                 default_pagination_size: int = 20, max_pagination_size: int = 100):
        """
        Initialize API framework.

        Args:
            app: WolfPy application instance
            prefix: API URL prefix
            version: API version
            enable_rate_limiting: Whether to enable rate limiting
            enable_versioning: Whether to enable API versioning
            default_pagination_size: Default pagination size
            max_pagination_size: Maximum pagination size
        """
        self.app = app
        self.prefix = prefix.rstrip('/')
        self.version = version
        self.endpoints = []
        self.documentation = APIDocumentation()

        # Advanced features
        self.enable_rate_limiting = enable_rate_limiting
        self.enable_versioning = enable_versioning
        self.default_pagination_size = default_pagination_size
        self.max_pagination_size = max_pagination_size

        # Initialize components
        if self.enable_rate_limiting:
            self.rate_limiter = RateLimiter()

        if self.enable_versioning:
            self.version_manager = APIVersionManager()
            self.version_manager.register_version(version, is_default=True)

        # Default serializer
        self.default_serializer = APISerializer()

        # Register API routes
        self._register_api_routes()
    
    def endpoint(self, path: str, methods: List[str] = None,
                summary: str = "", description: str = "",
                request_model: Type[APIModel] = None,
                response_model: Type[APIModel] = None,
                tags: List[str] = None,
                rate_limit: Tuple[int, int] = None,
                enable_pagination: bool = False,
                serializer: APISerializer = None):
        """
        Decorator for API endpoints.

        Args:
            path: Endpoint path
            methods: HTTP methods
            summary: Short description
            description: Detailed description
            request_model: Request body model
            response_model: Response model
            tags: Endpoint tags
            rate_limit: Tuple of (max_requests, window_seconds)
            enable_pagination: Whether to enable automatic pagination
            serializer: Custom serializer for responses
        """
        if methods is None:
            methods = ['GET']

        def decorator(func: Callable):
            # Create API endpoint
            full_path = f"{self.prefix}/{self.version}{path}"

            for method in methods:
                endpoint = APIEndpoint(
                    path=full_path,
                    method=method,
                    handler=func,
                    summary=summary,
                    description=description,
                    request_model=request_model,
                    response_model=response_model,
                    tags=tags
                )

                self.endpoints.append(endpoint)
                self.documentation.add_endpoint(endpoint)

                # Create wrapper function
                @wraps(func)
                def wrapper(request: Request, **kwargs):
                    try:
                        # Rate limiting
                        if self.enable_rate_limiting and rate_limit:
                            client_id = self._get_client_id(request)
                            limiter = RateLimiter(rate_limit[0], rate_limit[1])
                            allowed, retry_after = limiter.is_allowed(client_id)

                            if not allowed:
                                response = Response.json(
                                    create_error_response(RateLimitError(retry_after=retry_after)),
                                    status=429
                                )
                                if retry_after:
                                    response.headers['Retry-After'] = str(retry_after)
                                return response

                        # API versioning
                        if self.enable_versioning:
                            api_version = self.version_manager.get_version_from_request(request)
                            if self.version_manager.is_version_deprecated(api_version):
                                # Add deprecation warning header
                                pass  # Would add warning header

                        # Parse request body if model is specified
                        if endpoint.request_model and request.method in ['POST', 'PUT', 'PATCH']:
                            try:
                                body_data = request.get_json()
                                if body_data:
                                    request.api_data = endpoint.request_model.from_dict(body_data)
                                else:
                                    request.api_data = None
                            except ValidationError as e:
                                return Response.json(
                                    create_error_response(e),
                                    status=e.status_code
                                )
                            except Exception as e:
                                return Response.json(
                                    create_error_response(APIError("Invalid JSON", 400)),
                                    status=400
                                )

                        # Add pagination if enabled
                        if enable_pagination:
                            request.pagination = PaginationInfo.from_request(
                                request,
                                self.default_pagination_size,
                                self.max_pagination_size
                            )

                        # Call handler
                        result = func(request, **kwargs)

                        # Handle response
                        if isinstance(result, Response):
                            return result
                        elif isinstance(result, APIModel):
                            data = result.to_dict()
                            return Response.json(data)
                        elif isinstance(result, dict):
                            return Response.json(result)
                        elif isinstance(result, (list, tuple)) and enable_pagination:
                            # Auto-paginate list results
                            used_serializer = serializer or self.default_serializer
                            paginated = paginate_data(list(result), request.pagination, used_serializer)
                            return Response.json(paginated)
                        elif serializer:
                            # Use custom serializer
                            serialized = serializer.serialize(result)
                            return Response.json(serialized)
                        else:
                            return Response.json({'result': result})

                    except APIError as e:
                        return Response.json(
                            create_error_response(e),
                            status=e.status_code
                        )

                    except Exception as e:
                        error_response = create_error_response(e, include_traceback=self.app.debug)
                        return Response.json(error_response, status=500)

                # Register route with app
                self.app.route(full_path, methods=[method])(wrapper)

            return func

        return decorator

    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        # Try to get user ID first
        if hasattr(request, 'user') and request.user:
            return f"user:{request.user.id}"

        # Fall back to IP address
        return f"ip:{request.remote_addr}"

    def get(self, path: str, **kwargs):
        """Convenience decorator for GET endpoints."""
        return self.endpoint(path, methods=['GET'], **kwargs)

    def post(self, path: str, **kwargs):
        """Convenience decorator for POST endpoints."""
        return self.endpoint(path, methods=['POST'], **kwargs)

    def put(self, path: str, **kwargs):
        """Convenience decorator for PUT endpoints."""
        return self.endpoint(path, methods=['PUT'], **kwargs)

    def patch(self, path: str, **kwargs):
        """Convenience decorator for PATCH endpoints."""
        return self.endpoint(path, methods=['PATCH'], **kwargs)

    def delete(self, path: str, **kwargs):
        """Convenience decorator for DELETE endpoints."""
        return self.endpoint(path, methods=['DELETE'], **kwargs)

    def paginated_get(self, path: str, **kwargs):
        """Convenience decorator for paginated GET endpoints."""
        kwargs['enable_pagination'] = True
        return self.get(path, **kwargs)

    def rate_limited(self, max_requests: int = 100, window_seconds: int = 3600):
        """Decorator to add rate limiting to endpoints."""
        def decorator(func):
            # Store rate limit info on function
            func._rate_limit = (max_requests, window_seconds)
            return func
        return decorator
    
    def _register_api_routes(self):
        """Register API documentation routes."""
        
        @self.app.route(f"{self.prefix}/docs")
        def api_docs(request):
            """API documentation page."""
            return Response(self._generate_docs_html())
        
        @self.app.route(f"{self.prefix}/openapi.json")
        def openapi_spec(request):
            """OpenAPI specification."""
            return Response.json(self.documentation.generate_openapi_spec())
    
    def _generate_docs_html(self) -> str:
        """Generate HTML documentation page."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>API Documentation</title>
            <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3.25.0/swagger-ui.css" />
        </head>
        <body>
            <div id="swagger-ui"></div>
            <script src="https://unpkg.com/swagger-ui-dist@3.25.0/swagger-ui-bundle.js"></script>
            <script>
                SwaggerUIBundle({{
                    url: '{self.prefix}/openapi.json',
                    dom_id: '#swagger-ui',
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIBundle.presets.standalone
                    ]
                }});
            </script>
        </body>
        </html>
        """


class APIResponseFormatter:
    """
    Enhanced API response formatter with consistent structure.
    """

    def __init__(self, include_metadata: bool = True):
        self.include_metadata = include_metadata

    def success_response(self, data: Any = None, message: str = "Success",
                        status: int = 200, meta: Dict[str, Any] = None) -> Dict[str, Any]:
        """Format successful API response."""
        response = {
            'success': True,
            'status': status,
            'message': message
        }

        if data is not None:
            response['data'] = data

        if self.include_metadata and meta:
            response['meta'] = meta

        if self.include_metadata:
            response['timestamp'] = datetime.now().isoformat()

        return response

    def error_response(self, message: str, status: int = 400,
                      error_code: str = None, details: Dict[str, Any] = None) -> Dict[str, Any]:
        """Format error API response."""
        response = {
            'success': False,
            'status': status,
            'message': message
        }

        if error_code:
            response['error_code'] = error_code

        if details:
            response['details'] = details

        if self.include_metadata:
            response['timestamp'] = datetime.now().isoformat()

        return response

    def paginated_response(self, data: List[Any], page: int, per_page: int,
                          total: int, message: str = "Success") -> Dict[str, Any]:
        """Format paginated API response."""
        total_pages = (total + per_page - 1) // per_page

        response = self.success_response(data, message)
        response['pagination'] = {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }

        return response


class APIValidator:
    """
    Enhanced API request validator with comprehensive validation rules.
    """

    def __init__(self):
        self.validation_rules = {
            'required': self._validate_required,
            'type': self._validate_type,
            'min_length': self._validate_min_length,
            'max_length': self._validate_max_length,
            'pattern': self._validate_pattern,
            'enum': self._validate_enum,
            'range': self._validate_range,
            'email': self._validate_email,
            'url': self._validate_url,
            'custom': self._validate_custom
        }

    def validate_request_data(self, data: Dict[str, Any],
                            schema: Dict[str, Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """
        Validate request data against schema.

        Args:
            data: Request data to validate
            schema: Validation schema

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        for field_name, field_rules in schema.items():
            field_value = data.get(field_name)

            for rule_name, rule_value in field_rules.items():
                if rule_name in self.validation_rules:
                    try:
                        is_valid, error_msg = self.validation_rules[rule_name](
                            field_name, field_value, rule_value
                        )
                        if not is_valid:
                            errors.append(error_msg)
                    except Exception as e:
                        errors.append(f"Validation error for {field_name}: {str(e)}")

        return len(errors) == 0, errors

    def _validate_required(self, field_name: str, value: Any, required: bool) -> Tuple[bool, str]:
        """Validate required field."""
        if required and (value is None or value == ''):
            return False, f"Field '{field_name}' is required"
        return True, ""

    def _validate_type(self, field_name: str, value: Any, expected_type: str) -> Tuple[bool, str]:
        """Validate field type."""
        if value is None:
            return True, ""

        type_map = {
            'string': str,
            'integer': int,
            'float': float,
            'boolean': bool,
            'list': list,
            'dict': dict
        }

        expected_python_type = type_map.get(expected_type)
        if expected_python_type and not isinstance(value, expected_python_type):
            return False, f"Field '{field_name}' must be of type {expected_type}"

        return True, ""

    def _validate_min_length(self, field_name: str, value: Any, min_length: int) -> Tuple[bool, str]:
        """Validate minimum length."""
        if value is not None and len(str(value)) < min_length:
            return False, f"Field '{field_name}' must be at least {min_length} characters"
        return True, ""

    def _validate_max_length(self, field_name: str, value: Any, max_length: int) -> Tuple[bool, str]:
        """Validate maximum length."""
        if value is not None and len(str(value)) > max_length:
            return False, f"Field '{field_name}' must be at most {max_length} characters"
        return True, ""

    def _validate_pattern(self, field_name: str, value: Any, pattern: str) -> Tuple[bool, str]:
        """Validate regex pattern."""
        if value is not None and not re.match(pattern, str(value)):
            return False, f"Field '{field_name}' does not match required pattern"
        return True, ""

    def _validate_enum(self, field_name: str, value: Any, enum_values: List[Any]) -> Tuple[bool, str]:
        """Validate enum values."""
        if value is not None and value not in enum_values:
            return False, f"Field '{field_name}' must be one of {enum_values}"
        return True, ""

    def _validate_range(self, field_name: str, value: Any, range_spec: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate numeric range."""
        if value is None:
            return True, ""

        try:
            numeric_value = float(value)
            min_val = range_spec.get('min')
            max_val = range_spec.get('max')

            if min_val is not None and numeric_value < min_val:
                return False, f"Field '{field_name}' must be at least {min_val}"

            if max_val is not None and numeric_value > max_val:
                return False, f"Field '{field_name}' must be at most {max_val}"

        except (ValueError, TypeError):
            return False, f"Field '{field_name}' must be a valid number"

        return True, ""

    def _validate_email(self, field_name: str, value: Any, validate_email: bool) -> Tuple[bool, str]:
        """Validate email format."""
        if not validate_email or value is None:
            return True, ""

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, str(value)):
            return False, f"Field '{field_name}' must be a valid email address"

        return True, ""

    def _validate_url(self, field_name: str, value: Any, validate_url: bool) -> Tuple[bool, str]:
        """Validate URL format."""
        if not validate_url or value is None:
            return True, ""

        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, str(value)):
            return False, f"Field '{field_name}' must be a valid URL"

        return True, ""

    def _validate_custom(self, field_name: str, value: Any, custom_func: Callable) -> Tuple[bool, str]:
        """Validate using custom function."""
        try:
            result = custom_func(value)
            if isinstance(result, bool):
                return result, f"Field '{field_name}' failed custom validation" if not result else ""
            elif isinstance(result, tuple) and len(result) == 2:
                return result
            else:
                return True, ""
        except Exception as e:
            return False, f"Custom validation error for '{field_name}': {str(e)}"


class APIRateLimiter:
    """
    Rate limiter for API endpoints.
    """

    def __init__(self, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.request_counts = {}
        self.request_times = {}

    def is_allowed(self, client_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed for client.

        Args:
            client_id: Unique client identifier (IP, user ID, etc.)

        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        current_time = time.time()

        if client_id not in self.request_counts:
            self.request_counts[client_id] = {'minute': [], 'hour': []}

        # Clean old requests
        self._clean_old_requests(client_id, current_time)

        # Check limits
        minute_count = len(self.request_counts[client_id]['minute'])
        hour_count = len(self.request_counts[client_id]['hour'])

        rate_limit_info = {
            'requests_per_minute': minute_count,
            'requests_per_hour': hour_count,
            'limit_per_minute': self.requests_per_minute,
            'limit_per_hour': self.requests_per_hour,
            'reset_time': int(current_time + 60)  # Next minute
        }

        if minute_count >= self.requests_per_minute:
            return False, rate_limit_info

        if hour_count >= self.requests_per_hour:
            return False, rate_limit_info

        # Record request
        self.request_counts[client_id]['minute'].append(current_time)
        self.request_counts[client_id]['hour'].append(current_time)

        return True, rate_limit_info

    def _clean_old_requests(self, client_id: str, current_time: float):
        """Remove old request records."""
        minute_ago = current_time - 60
        hour_ago = current_time - 3600

        # Clean minute records
        self.request_counts[client_id]['minute'] = [
            t for t in self.request_counts[client_id]['minute'] if t > minute_ago
        ]

        # Clean hour records
        self.request_counts[client_id]['hour'] = [
            t for t in self.request_counts[client_id]['hour'] if t > hour_ago
        ]





class APISerializer:
    """
    Advanced API serializer for complex data structures.
    """

    def __init__(self, fields: Dict[str, Any] = None,
                 exclude: List[str] = None, nested: Dict[str, 'APISerializer'] = None,
                 include_fields: List[str] = None, exclude_fields: List[str] = None):
        self.fields = fields or {}
        self.exclude = exclude or exclude_fields or []
        self.include_fields = include_fields
        self.nested = nested or {}

    def serialize(self, data: Any, many: bool = False) -> Any:
        """Serialize data to JSON-compatible format."""
        if many:
            return [self._serialize_single(item) for item in data]
        return self._serialize_single(data)

    def _serialize_single(self, obj: Any) -> Dict[str, Any]:
        """Serialize a single object."""
        if hasattr(obj, '__dict__'):
            # Handle model instances
            result = {}
            for key, value in obj.__dict__.items():
                # Skip private fields and excluded fields
                if key.startswith('_') or key in self.exclude:
                    continue

                # If include_fields is specified, only include those fields
                if self.include_fields and key not in self.include_fields:
                    continue

                # Apply field transformations
                if key in self.fields:
                    transformer = self.fields[key]
                    if callable(transformer):
                        value = transformer(value)

                # Handle nested serializers
                if key in self.nested:
                    nested_serializer = self.nested[key]
                    value = nested_serializer.serialize(value)

                # Handle special types
                value = self._serialize_value(value)
                result[key] = value

            return result
        elif isinstance(obj, dict):
            # Handle dictionaries
            result = {}
            for key, value in obj.items():
                # Skip private fields and excluded fields
                if key.startswith('_') or key in self.exclude:
                    continue

                # If include_fields is specified, only include those fields
                if self.include_fields and key not in self.include_fields:
                    continue

                # Apply field transformations
                if key in self.fields:
                    transformer = self.fields[key]
                    if callable(transformer):
                        value = transformer(value)

                # Handle nested serializers
                if key in self.nested:
                    nested_serializer = self.nested[key]
                    value = nested_serializer.serialize(value)

                result[key] = self._serialize_value(value)
            return result
        else:
            return self._serialize_value(obj)

    def _serialize_value(self, value: Any) -> Any:
        """Serialize individual values."""
        if isinstance(value, (str, int, float, bool, type(None))):
            return value
        elif isinstance(value, (list, tuple)):
            return [self._serialize_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        elif hasattr(value, 'isoformat'):  # datetime objects
            return value.isoformat()
        elif hasattr(value, '__dict__'):
            return self._serialize_single(value)
        else:
            return str(value)

    def deserialize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Deserialize data from JSON format."""
        result = {}

        for key, value in data.items():
            if key in self.exclude:
                continue

            # Apply field transformations
            if key in self.fields:
                transformer = self.fields[key]
                if callable(transformer):
                    value = transformer(value)

            # Handle nested deserializers
            if key in self.nested:
                nested_serializer = self.nested[key]
                value = nested_serializer.deserialize(value)

            result[key] = value

        return result


class APIDocumentationGenerator:
    """
    Advanced API documentation generator with OpenAPI 3.0 support.
    """

    def __init__(self, title: str = "API Documentation", version: str = "1.0.0",
                 description: str = "API Documentation"):
        self.title = title
        self.version = version
        self.description = description
        self.endpoints = {}
        self.schemas = {}
        self.security_schemes = {}

    def add_endpoint(self, path: str, method: str, endpoint_info: Dict[str, Any]):
        """Add endpoint documentation."""
        if path not in self.endpoints:
            self.endpoints[path] = {}

        self.endpoints[path][method.lower()] = {
            'summary': endpoint_info.get('summary', ''),
            'description': endpoint_info.get('description', ''),
            'parameters': endpoint_info.get('parameters', []),
            'requestBody': endpoint_info.get('request_body'),
            'responses': endpoint_info.get('responses', {}),
            'tags': endpoint_info.get('tags', []),
            'security': endpoint_info.get('security', [])
        }

    def add_schema(self, name: str, schema: Dict[str, Any]):
        """Add data schema definition."""
        self.schemas[name] = schema

    def add_security_scheme(self, name: str, scheme: Dict[str, Any]):
        """Add security scheme definition."""
        self.security_schemes[name] = scheme

    def generate_openapi_spec(self) -> Dict[str, Any]:
        """Generate OpenAPI 3.0 specification."""
        spec = {
            'openapi': '3.0.0',
            'info': {
                'title': self.title,
                'version': self.version,
                'description': self.description
            },
            'paths': self.endpoints,
            'components': {
                'schemas': self.schemas,
                'securitySchemes': self.security_schemes
            }
        }

        return spec

    def generate_html_docs(self) -> str:
        """Generate HTML documentation with Swagger UI."""
        spec = self.generate_openapi_spec()

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{self.title}</title>
            <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui.css" />
            <style>
                html {{ box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }}
                *, *:before, *:after {{ box-sizing: inherit; }}
                body {{ margin:0; background: #fafafa; }}
            </style>
        </head>
        <body>
            <div id="swagger-ui"></div>
            <script src="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui-bundle.js"></script>
            <script src="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui-standalone-preset.js"></script>
            <script>
                window.onload = function() {{
                    const ui = SwaggerUIBundle({{
                        spec: {json.dumps(spec)},
                        dom_id: '#swagger-ui',
                        deepLinking: true,
                        presets: [
                            SwaggerUIBundle.presets.apis,
                            SwaggerUIStandalonePreset
                        ],
                        plugins: [
                            SwaggerUIBundle.plugins.DownloadUrl
                        ],
                        layout: "StandaloneLayout"
                    }});
                }};
            </script>
        </body>
        </html>
        """

        return html


class AdvancedRateLimiter:
    """
    Advanced rate limiter with multiple strategies and sliding windows.
    """

    def __init__(self, strategies: Dict[str, Dict[str, Any]] = None):
        self.strategies = strategies or {
            'default': {'requests': 100, 'window': 3600, 'type': 'sliding'}
        }
        self.request_logs = defaultdict(list)
        self.blocked_clients = {}

    def is_allowed(self, client_id: str, strategy: str = 'default') -> Tuple[bool, Dict[str, Any]]:
        """Check if request is allowed under rate limiting."""
        if strategy not in self.strategies:
            strategy = 'default'

        config = self.strategies[strategy]
        current_time = time.time()

        # Check if client is temporarily blocked
        if client_id in self.blocked_clients:
            if current_time < self.blocked_clients[client_id]:
                return False, {'blocked_until': self.blocked_clients[client_id]}
            else:
                del self.blocked_clients[client_id]

        # Clean old requests
        window_start = current_time - config['window']
        self.request_logs[client_id] = [
            timestamp for timestamp in self.request_logs[client_id]
            if timestamp > window_start
        ]

        # Check rate limit
        request_count = len(self.request_logs[client_id])

        if request_count >= config['requests']:
            # Block client for a period
            self.blocked_clients[client_id] = current_time + 300  # 5 minutes
            return False, {
                'rate_limited': True,
                'requests_made': request_count,
                'limit': config['requests'],
                'window': config['window'],
                'blocked_until': self.blocked_clients[client_id]
            }

        # Record request
        self.request_logs[client_id].append(current_time)

        return True, {
            'requests_made': request_count + 1,
            'limit': config['requests'],
            'window': config['window'],
            'remaining': config['requests'] - request_count - 1
        }

    def add_strategy(self, name: str, requests: int, window: int,
                    rate_type: str = 'sliding'):
        """Add a new rate limiting strategy."""
        self.strategies[name] = {
            'requests': requests,
            'window': window,
            'type': rate_type
        }

    def get_client_stats(self, client_id: str) -> Dict[str, Any]:
        """Get statistics for a specific client."""
        current_time = time.time()
        recent_requests = [
            timestamp for timestamp in self.request_logs[client_id]
            if timestamp > current_time - 3600  # Last hour
        ]

        return {
            'total_requests': len(self.request_logs[client_id]),
            'recent_requests': len(recent_requests),
            'is_blocked': client_id in self.blocked_clients,
            'blocked_until': self.blocked_clients.get(client_id)
        }


class GraphQLSchema:
    """
    GraphQL schema definition and execution engine.
    """

    def __init__(self):
        self.types = {}
        self.queries = {}
        self.mutations = {}
        self.subscriptions = {}
        self.resolvers = {}

    def add_type(self, name: str, fields: Dict[str, str]):
        """Add a GraphQL type definition."""
        self.types[name] = fields

    def add_query(self, name: str, return_type: str, args: Dict[str, str] = None):
        """Add a GraphQL query."""
        self.queries[name] = {
            'return_type': return_type,
            'args': args or {}
        }

    def add_mutation(self, name: str, return_type: str, args: Dict[str, str] = None):
        """Add a GraphQL mutation."""
        self.mutations[name] = {
            'return_type': return_type,
            'args': args or {}
        }

    def add_resolver(self, field_name: str, resolver_func: Callable):
        """Add a resolver function for a field."""
        self.resolvers[field_name] = resolver_func

    def generate_schema_sdl(self) -> str:
        """Generate GraphQL Schema Definition Language."""
        sdl_parts = []

        # Add types
        for type_name, fields in self.types.items():
            field_definitions = []
            for field_name, field_type in fields.items():
                field_definitions.append(f"  {field_name}: {field_type}")

            sdl_parts.append(f"type {type_name} {{\n" + "\n".join(field_definitions) + "\n}")

        # Add Query type
        if self.queries:
            query_fields = []
            for query_name, query_def in self.queries.items():
                args_str = ""
                if query_def['args']:
                    args_list = [f"{arg_name}: {arg_type}" for arg_name, arg_type in query_def['args'].items()]
                    args_str = f"({', '.join(args_list)})"

                query_fields.append(f"  {query_name}{args_str}: {query_def['return_type']}")

            sdl_parts.append("type Query {\n" + "\n".join(query_fields) + "\n}")

        # Add Mutation type
        if self.mutations:
            mutation_fields = []
            for mutation_name, mutation_def in self.mutations.items():
                args_str = ""
                if mutation_def['args']:
                    args_list = [f"{arg_name}: {arg_type}" for arg_name, arg_type in mutation_def['args'].items()]
                    args_str = f"({', '.join(args_list)})"

                mutation_fields.append(f"  {mutation_name}{args_str}: {mutation_def['return_type']}")

            sdl_parts.append("type Mutation {\n" + "\n".join(mutation_fields) + "\n}")

        return "\n\n".join(sdl_parts)

    def execute_query(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a GraphQL query (simplified implementation)."""
        # This is a very simplified GraphQL execution
        # In a real implementation, you'd use a proper GraphQL library

        try:
            # Parse query (simplified)
            query = query.strip()

            if query.startswith('query') or query.startswith('{'):
                return self._execute_query_operation(query, variables or {})
            elif query.startswith('mutation'):
                return self._execute_mutation_operation(query, variables or {})
            else:
                return {'errors': [{'message': 'Invalid query operation'}]}

        except Exception as e:
            return {'errors': [{'message': str(e)}]}

    def _execute_query_operation(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a query operation."""
        # Simplified query execution
        # Extract field names (very basic parsing)
        import re

        # Find field requests
        field_matches = re.findall(r'(\w+)(?:\s*\([^)]*\))?\s*{?', query)

        result_data = {}

        for field_name in field_matches:
            if field_name in ['query', 'Query']:
                continue

            if field_name in self.resolvers:
                try:
                    # Call resolver
                    resolver_result = self.resolvers[field_name](variables)
                    result_data[field_name] = resolver_result
                except Exception as e:
                    return {'errors': [{'message': f'Resolver error for {field_name}: {str(e)}'}]}
            else:
                result_data[field_name] = f"No resolver for {field_name}"

        return {'data': result_data}

    def _execute_mutation_operation(self, mutation: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a mutation operation."""
        # Similar to query execution but for mutations
        import re

        field_matches = re.findall(r'(\w+)(?:\s*\([^)]*\))?\s*{?', mutation)

        result_data = {}

        for field_name in field_matches:
            if field_name in ['mutation', 'Mutation']:
                continue

            if field_name in self.resolvers:
                try:
                    resolver_result = self.resolvers[field_name](variables)
                    result_data[field_name] = resolver_result
                except Exception as e:
                    return {'errors': [{'message': f'Mutation error for {field_name}: {str(e)}'}]}
            else:
                result_data[field_name] = f"No resolver for {field_name}"

        return {'data': result_data}


class APIGateway:
    """
    API Gateway with routing, transformation, and monitoring.
    """

    def __init__(self):
        self.routes = []
        self.transformations = {}
        self.rate_limiters = {}
        self.metrics = defaultdict(int)
        self.request_logs = []

    def add_route(self, pattern: str, target_url: str, methods: List[str] = None,
                 rate_limit: Dict[str, Any] = None, transformations: Dict[str, Any] = None):
        """Add a route to the gateway."""
        route = {
            'pattern': pattern,
            'target_url': target_url,
            'methods': methods or ['GET'],
            'rate_limit': rate_limit,
            'transformations': transformations or {}
        }
        self.routes.append(route)

        # Set up rate limiter if specified
        if rate_limit:
            self.rate_limiters[pattern] = AdvancedRateLimiter({
                'default': rate_limit
            })

    def process_request(self, request: Request) -> Optional[Response]:
        """Process incoming request through the gateway."""
        start_time = time.time()

        # Find matching route
        matching_route = None
        for route in self.routes:
            if self._match_route(route['pattern'], request.path):
                if request.method in route['methods']:
                    matching_route = route
                    break

        if not matching_route:
            return Response.json({'error': 'Route not found'}, status=404)

        # Check rate limiting
        if matching_route['pattern'] in self.rate_limiters:
            rate_limiter = self.rate_limiters[matching_route['pattern']]
            client_id = request.remote_addr

            is_allowed, rate_info = rate_limiter.is_allowed(client_id)
            if not is_allowed:
                return Response.json({
                    'error': 'Rate limit exceeded',
                    'rate_limit_info': rate_info
                }, status=429)

        # Apply request transformations
        transformed_request = self._apply_request_transformations(
            request, matching_route['transformations']
        )

        # Forward request (simplified - would use actual HTTP client)
        try:
            response_data = self._forward_request(matching_route['target_url'], transformed_request)

            # Apply response transformations
            transformed_response = self._apply_response_transformations(
                response_data, matching_route['transformations']
            )

            # Log metrics
            self.metrics['total_requests'] += 1
            self.metrics['successful_requests'] += 1

            processing_time = time.time() - start_time
            self.request_logs.append({
                'timestamp': time.time(),
                'path': request.path,
                'method': request.method,
                'target': matching_route['target_url'],
                'processing_time': processing_time,
                'status': 'success'
            })

            return Response.json(transformed_response)

        except Exception as e:
            self.metrics['failed_requests'] += 1

            self.request_logs.append({
                'timestamp': time.time(),
                'path': request.path,
                'method': request.method,
                'target': matching_route['target_url'],
                'processing_time': time.time() - start_time,
                'status': 'error',
                'error': str(e)
            })

            return Response.json({'error': 'Gateway error', 'details': str(e)}, status=502)

    def _match_route(self, pattern: str, path: str) -> bool:
        """Check if path matches route pattern."""
        # Simple pattern matching (could be enhanced with regex)
        if '*' in pattern:
            prefix = pattern.replace('*', '')
            return path.startswith(prefix)
        return pattern == path

    def _apply_request_transformations(self, request: Request, transformations: Dict[str, Any]) -> Request:
        """Apply transformations to request."""
        # Simplified transformation logic
        return request

    def _apply_response_transformations(self, response_data: Any, transformations: Dict[str, Any]) -> Any:
        """Apply transformations to response."""
        # Simplified transformation logic
        return response_data

    def _forward_request(self, target_url: str, request: Request) -> Dict[str, Any]:
        """Forward request to target service."""
        # Simplified request forwarding
        # In real implementation, would use HTTP client library
        return {'message': f'Forwarded to {target_url}', 'original_path': request.path}

    def get_metrics(self) -> Dict[str, Any]:
        """Get gateway metrics."""
        recent_logs = [log for log in self.request_logs if time.time() - log['timestamp'] < 3600]

        return {
            'total_requests': self.metrics['total_requests'],
            'successful_requests': self.metrics['successful_requests'],
            'failed_requests': self.metrics['failed_requests'],
            'success_rate': (self.metrics['successful_requests'] / max(self.metrics['total_requests'], 1)) * 100,
            'recent_requests': len(recent_logs),
            'average_processing_time': sum(log['processing_time'] for log in recent_logs) / max(len(recent_logs), 1)
        }


class WebhookManager:
    """
    Advanced webhook management system.
    """

    def __init__(self):
        self.webhooks = {}
        self.delivery_attempts = defaultdict(list)
        self.failed_deliveries = defaultdict(list)
        self.webhook_stats = defaultdict(lambda: defaultdict(int))

    def register_webhook(self, webhook_id: str, url: str, events: List[str],
                        secret: str = None, retry_config: Dict[str, Any] = None) -> str:
        """Register a new webhook."""
        import secrets

        if not webhook_id:
            webhook_id = secrets.token_urlsafe(16)

        webhook = {
            'id': webhook_id,
            'url': url,
            'events': events,
            'secret': secret or secrets.token_urlsafe(32),
            'created_at': time.time(),
            'active': True,
            'retry_config': retry_config or {
                'max_attempts': 3,
                'retry_delay': 60,  # seconds
                'backoff_multiplier': 2
            }
        }

        self.webhooks[webhook_id] = webhook
        return webhook_id

    def trigger_webhook(self, event_type: str, data: Dict[str, Any]) -> List[str]:
        """Trigger webhooks for a specific event."""
        triggered_webhooks = []

        for webhook_id, webhook in self.webhooks.items():
            if not webhook['active']:
                continue

            if event_type in webhook['events'] or '*' in webhook['events']:
                self._deliver_webhook(webhook_id, event_type, data)
                triggered_webhooks.append(webhook_id)

        return triggered_webhooks

    def _deliver_webhook(self, webhook_id: str, event_type: str, data: Dict[str, Any]):
        """Deliver webhook payload to endpoint."""
        webhook = self.webhooks[webhook_id]

        payload = {
            'event_type': event_type,
            'webhook_id': webhook_id,
            'timestamp': time.time(),
            'data': data
        }

        # Generate signature
        signature = self._generate_signature(payload, webhook['secret'])

        # Attempt delivery
        self._attempt_delivery(webhook_id, webhook['url'], payload, signature)

    def _attempt_delivery(self, webhook_id: str, url: str, payload: Dict[str, Any], signature: str):
        """Attempt webhook delivery with retry logic."""
        webhook = self.webhooks[webhook_id]
        retry_config = webhook['retry_config']

        attempt_count = len(self.delivery_attempts[webhook_id])

        try:
            # Simulate HTTP request (in real implementation, use requests library)
            success = self._send_webhook_request(url, payload, signature)

            if success:
                self.delivery_attempts[webhook_id].append({
                    'timestamp': time.time(),
                    'attempt': attempt_count + 1,
                    'status': 'success'
                })
                self.webhook_stats[webhook_id]['successful_deliveries'] += 1
            else:
                raise Exception("Webhook delivery failed")

        except Exception as e:
            self.delivery_attempts[webhook_id].append({
                'timestamp': time.time(),
                'attempt': attempt_count + 1,
                'status': 'failed',
                'error': str(e)
            })

            self.webhook_stats[webhook_id]['failed_deliveries'] += 1

            # Schedule retry if within limits
            if attempt_count < retry_config['max_attempts'] - 1:
                retry_delay = retry_config['retry_delay'] * (retry_config['backoff_multiplier'] ** attempt_count)
                self._schedule_retry(webhook_id, url, payload, signature, retry_delay)
            else:
                self.failed_deliveries[webhook_id].append({
                    'timestamp': time.time(),
                    'payload': payload,
                    'final_error': str(e)
                })

    def _send_webhook_request(self, url: str, payload: Dict[str, Any], signature: str) -> bool:
        """Send webhook HTTP request."""
        # Simplified webhook delivery
        # In real implementation, would use requests library with proper headers

        # Simulate success/failure based on URL
        if 'fail' in url.lower():
            return False
        return True

    def _generate_signature(self, payload: Dict[str, Any], secret: str) -> str:
        """Generate webhook signature for verification."""
        import hmac
        import hashlib
        import json

        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        return f"sha256={signature}"

    def _schedule_retry(self, webhook_id: str, url: str, payload: Dict[str, Any],
                      signature: str, delay: float):
        """Schedule webhook retry (simplified)."""
        # In real implementation, would use a task queue like Celery
        print(f"Scheduling retry for webhook {webhook_id} in {delay} seconds")

    def get_webhook_stats(self, webhook_id: str) -> Dict[str, Any]:
        """Get statistics for a specific webhook."""
        if webhook_id not in self.webhooks:
            return {'error': 'Webhook not found'}

        webhook = self.webhooks[webhook_id]
        stats = self.webhook_stats[webhook_id]
        attempts = self.delivery_attempts[webhook_id]
        failures = self.failed_deliveries[webhook_id]

        return {
            'webhook_id': webhook_id,
            'url': webhook['url'],
            'events': webhook['events'],
            'active': webhook['active'],
            'created_at': webhook['created_at'],
            'total_attempts': len(attempts),
            'successful_deliveries': stats['successful_deliveries'],
            'failed_deliveries': stats['failed_deliveries'],
            'success_rate': (stats['successful_deliveries'] / max(len(attempts), 1)) * 100,
            'recent_failures': len([f for f in failures if time.time() - f['timestamp'] < 3600])
        }

    def list_webhooks(self) -> List[Dict[str, Any]]:
        """List all registered webhooks."""
        return [
            {
                'id': webhook_id,
                'url': webhook['url'],
                'events': webhook['events'],
                'active': webhook['active'],
                'created_at': webhook['created_at']
            }
            for webhook_id, webhook in self.webhooks.items()
        ]

    def deactivate_webhook(self, webhook_id: str) -> bool:
        """Deactivate a webhook."""
        if webhook_id in self.webhooks:
            self.webhooks[webhook_id]['active'] = False
            return True
        return False

    def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook."""
        if webhook_id in self.webhooks:
            del self.webhooks[webhook_id]
            # Clean up related data
            if webhook_id in self.delivery_attempts:
                del self.delivery_attempts[webhook_id]
            if webhook_id in self.failed_deliveries:
                del self.failed_deliveries[webhook_id]
            if webhook_id in self.webhook_stats:
                del self.webhook_stats[webhook_id]
            return True
        return False


class APIMonitoringSystem:
    """
    Comprehensive API monitoring and analytics system.
    """

    def __init__(self):
        self.request_metrics = defaultdict(lambda: defaultdict(int))
        self.response_times = defaultdict(list)
        self.error_logs = []
        self.endpoint_stats = defaultdict(lambda: {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0.0,
            'last_accessed': 0
        })
        self.alerts = []
        self.thresholds = {
            'response_time': 1000,  # ms
            'error_rate': 5,  # percentage
            'requests_per_minute': 1000
        }

    def record_request(self, endpoint: str, method: str, status_code: int,
                      response_time: float, user_agent: str = None, ip_address: str = None):
        """Record API request metrics."""
        current_time = time.time()
        endpoint_key = f"{method} {endpoint}"

        # Update endpoint stats
        stats = self.endpoint_stats[endpoint_key]
        stats['total_requests'] += 1
        stats['last_accessed'] = current_time

        if 200 <= status_code < 400:
            stats['successful_requests'] += 1
        else:
            stats['failed_requests'] += 1

            # Log error
            self.error_logs.append({
                'timestamp': current_time,
                'endpoint': endpoint,
                'method': method,
                'status_code': status_code,
                'response_time': response_time,
                'user_agent': user_agent,
                'ip_address': ip_address
            })

        # Update response times
        self.response_times[endpoint_key].append(response_time)

        # Keep only recent response times (last 1000)
        if len(self.response_times[endpoint_key]) > 1000:
            self.response_times[endpoint_key] = self.response_times[endpoint_key][-1000:]

        # Calculate average response time
        if self.response_times[endpoint_key]:
            stats['avg_response_time'] = sum(self.response_times[endpoint_key]) / len(self.response_times[endpoint_key])

        # Update general metrics
        self.request_metrics['total']['requests'] += 1
        self.request_metrics['status_codes'][status_code] += 1
        self.request_metrics['methods'][method] += 1

        # Check for alerts
        self._check_alerts(endpoint_key, stats, response_time)

    def _check_alerts(self, endpoint_key: str, stats: Dict[str, Any], response_time: float):
        """Check if any alert thresholds are exceeded."""
        current_time = time.time()

        # Check response time threshold
        if response_time > self.thresholds['response_time']:
            self.alerts.append({
                'type': 'high_response_time',
                'endpoint': endpoint_key,
                'value': response_time,
                'threshold': self.thresholds['response_time'],
                'timestamp': current_time
            })

        # Check error rate threshold
        if stats['total_requests'] > 10:  # Only check if we have enough data
            error_rate = (stats['failed_requests'] / stats['total_requests']) * 100
            if error_rate > self.thresholds['error_rate']:
                self.alerts.append({
                    'type': 'high_error_rate',
                    'endpoint': endpoint_key,
                    'value': error_rate,
                    'threshold': self.thresholds['error_rate'],
                    'timestamp': current_time
                })

        # Keep only recent alerts (last 100)
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data."""
        current_time = time.time()

        # Calculate recent metrics (last hour)
        recent_errors = [
            error for error in self.error_logs
            if current_time - error['timestamp'] < 3600
        ]

        recent_alerts = [
            alert for alert in self.alerts
            if current_time - alert['timestamp'] < 3600
        ]

        # Top endpoints by traffic
        top_endpoints = sorted(
            self.endpoint_stats.items(),
            key=lambda x: x[1]['total_requests'],
            reverse=True
        )[:10]

        # Slowest endpoints
        slowest_endpoints = sorted(
            [(k, v) for k, v in self.endpoint_stats.items() if v['avg_response_time'] > 0],
            key=lambda x: x[1]['avg_response_time'],
            reverse=True
        )[:10]

        return {
            'overview': {
                'total_requests': self.request_metrics['total']['requests'],
                'total_endpoints': len(self.endpoint_stats),
                'recent_errors': len(recent_errors),
                'recent_alerts': len(recent_alerts)
            },
            'top_endpoints': [
                {
                    'endpoint': endpoint,
                    'requests': stats['total_requests'],
                    'success_rate': (stats['successful_requests'] / max(stats['total_requests'], 1)) * 100,
                    'avg_response_time': stats['avg_response_time']
                }
                for endpoint, stats in top_endpoints
            ],
            'slowest_endpoints': [
                {
                    'endpoint': endpoint,
                    'avg_response_time': stats['avg_response_time'],
                    'total_requests': stats['total_requests']
                }
                for endpoint, stats in slowest_endpoints
            ],
            'recent_alerts': recent_alerts,
            'status_code_distribution': dict(self.request_metrics['status_codes']),
            'method_distribution': dict(self.request_metrics['methods'])
        }

    def get_endpoint_details(self, endpoint: str) -> Dict[str, Any]:
        """Get detailed metrics for a specific endpoint."""
        if endpoint not in self.endpoint_stats:
            return {'error': 'Endpoint not found'}

        stats = self.endpoint_stats[endpoint]
        response_times = self.response_times[endpoint]

        # Calculate percentiles
        if response_times:
            sorted_times = sorted(response_times)
            p50 = sorted_times[len(sorted_times) // 2]
            p95 = sorted_times[int(len(sorted_times) * 0.95)]
            p99 = sorted_times[int(len(sorted_times) * 0.99)]
        else:
            p50 = p95 = p99 = 0

        return {
            'endpoint': endpoint,
            'total_requests': stats['total_requests'],
            'successful_requests': stats['successful_requests'],
            'failed_requests': stats['failed_requests'],
            'success_rate': (stats['successful_requests'] / max(stats['total_requests'], 1)) * 100,
            'avg_response_time': stats['avg_response_time'],
            'response_time_percentiles': {
                'p50': p50,
                'p95': p95,
                'p99': p99
            },
            'last_accessed': stats['last_accessed']
        }
