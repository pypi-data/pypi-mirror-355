"""
WolfPy - A modular Python web framework built from scratch.

WolfPy is a lightweight, modular web framework that provides:
- WSGI-compliant application interface
- Flexible routing system
- Template engine integration
- Session and authentication management
- ORM and database layer
- Middleware support
- Static file handling

Example usage:
    from wolfpy import WolfPy

    app = WolfPy()

    @app.route('/')
    def home(request):
        return "Hello, WolfPy!"

    if __name__ == '__main__':
        app.run()
"""

from .app import WolfPy
from .core.request import Request
from .core.response import Response
from .core.router import Router
from .core.middleware import Middleware
from .core.auth import Auth
from .core.session import Session
from .core.database import Database
from .core.template_engine import TemplateEngine

# API functionality
from .core.api import APIFramework, APIModel, APIError, ValidationError
from .core.api_decorators import (
    api_route, get_route, post_route, put_route, patch_route, delete_route,
    APIRouter, json_response, validate_required_fields, paginate_data,
    enterprise_api_route, enterprise_features
)

# Enhanced security features
from .core.security_enhanced import (
    SecurityConfig, InputValidator, EnhancedRateLimiter,
    ContentSecurityPolicy, SecurityHeadersManager,
    security_config, input_validator, rate_limiter, csp_manager, security_headers
)

# Enhanced middleware
from .core.middleware_enhanced import (
    BaseEnhancedMiddleware, RequestLoggingMiddleware, ErrorHandlingMiddleware,
    PerformanceMiddleware, MiddlewareManager, middleware_manager
)

# Performance monitoring
from .core.performance import (
    PerformanceManager, PerformanceProfiler, MemoryMonitor,
    performance_monitor, memory_cache, resource_monitor
)

# Advanced Phase 2-6 Improvements
from .core.advanced_middleware import (
    AdvancedMiddlewareBase, RequestTransformationMiddleware,
    ResponseCompressionMiddleware, AdvancedMiddlewareManager,
    advanced_middleware_manager
)
from .core.advanced_auth import (
    AdvancedPasswordPolicy, MFAManager, SessionSecurityManager,
    AdvancedAuthenticationManager, UserProfile, SessionData,
    advanced_auth_manager
)
from .core.advanced_database import (
    AdvancedQueryCache, AdvancedConnectionPool, QueryOptimizer,
    AdvancedDatabaseManager, QueryMetrics, get_advanced_db_manager
)

# Phase 8: Error Handling & Robustness
from .core.error_handling import (
    ErrorContext, TracebackFormatter, ErrorLogger, ValidationErrorHandler,
    ErrorPageManager, ExceptionMiddleware
)

# Phase 9: Documentation & Plugin System
from .core.docs import DocumentationSystem
from .core.plugins import PluginManager, PluginInfo

# Phase 10: Admin Dashboard
from .core.admin import AdminSite, ModelAdmin, AdminUser, site as admin_site, register as admin_register

# Phase 11: Real-Time Support (Async/WebSockets)
from .core.asgi import ASGIApplication
from .core.websocket import WebSocket, WebSocketManager
from .core.realtime import RealtimeManager, Room, Channel

__version__ = "0.1.0"
__author__ = "Manish"
__email__ = "manish@example.com"
__license__ = "MIT"

__all__ = [
    # Core framework
    "WolfPy",
    "Request",
    "Response",
    "Router",
    "Middleware",
    "Auth",
    "Session",
    "Database",
    "TemplateEngine",

    # API functionality
    "APIFramework",
    "APIModel",
    "APIError",
    "ValidationError",
    "api_route",
    "get_route",
    "post_route",
    "put_route",
    "patch_route",
    "delete_route",
    "APIRouter",
    "json_response",
    "validate_required_fields",
    "paginate_data",
    "enterprise_api_route",
    "enterprise_features",

    # Enhanced security
    "SecurityConfig",
    "InputValidator",
    "EnhancedRateLimiter",
    "ContentSecurityPolicy",
    "SecurityHeadersManager",
    "security_config",
    "input_validator",
    "rate_limiter",
    "csp_manager",
    "security_headers",

    # Enhanced middleware
    "BaseEnhancedMiddleware",
    "RequestLoggingMiddleware",
    "ErrorHandlingMiddleware",
    "PerformanceMiddleware",
    "MiddlewareManager",
    "middleware_manager",

    # Performance monitoring
    "PerformanceManager",
    "PerformanceProfiler",
    "MemoryMonitor",
    "performance_monitor",
    "memory_cache",
    "resource_monitor",

    # Advanced Phase 2-6 Improvements
    "AdvancedMiddlewareBase",
    "RequestTransformationMiddleware",
    "ResponseCompressionMiddleware",
    "AdvancedMiddlewareManager",
    "advanced_middleware_manager",
    "AdvancedPasswordPolicy",
    "MFAManager",
    "SessionSecurityManager",
    "AdvancedAuthenticationManager",
    "UserProfile",
    "SessionData",
    "advanced_auth_manager",
    "AdvancedQueryCache",
    "AdvancedConnectionPool",
    "QueryOptimizer",
    "AdvancedDatabaseManager",
    "QueryMetrics",
    "get_advanced_db_manager",

    # Phase 8: Error Handling & Robustness
    "ErrorContext",
    "TracebackFormatter",
    "ErrorLogger",
    "ValidationErrorHandler",
    "ErrorPageManager",
    "ExceptionMiddleware",

    # Phase 9: Documentation & Plugin System
    "DocumentationSystem",
    "PluginManager",
    "PluginInfo",

    # Phase 10: Admin Dashboard
    "AdminSite",
    "ModelAdmin",
    "AdminUser",
    "admin_site",
    "admin_register",

    # Phase 11: Real-Time Support (Async/WebSockets)
    "ASGIApplication",
    "WebSocket",
    "WebSocketManager",
    "RealtimeManager",
    "Room",
    "Channel",
]
