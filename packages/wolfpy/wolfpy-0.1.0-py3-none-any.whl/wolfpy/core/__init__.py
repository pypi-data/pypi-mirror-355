"""
FoxPy Core Module.

This package contains the core components of the FoxPy web framework:
- Router: URL routing and pattern matching
- Request: HTTP request handling and parsing
- Response: HTTP response generation
- Middleware: Request/response processing pipeline
- Auth: Authentication and authorization
- Session: Session management
- Database: ORM and database operations
- TemplateEngine: Template rendering
"""

from .router import Router
from .request import Request
from .response import Response
from .middleware import Middleware
from .auth import Auth
from .session import Session
from .database import Database
from .template_engine import TemplateEngine

__all__ = [
    "Router",
    "Request", 
    "Response",
    "Middleware",
    "Auth",
    "Session",
    "Database",
    "TemplateEngine",
]
