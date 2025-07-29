"""
WolfPy Database Adapters.

This module provides database adapters for different database backends.
"""

from .base import DatabaseAdapter
from .sqlite import SQLiteAdapter

try:
    from .postgresql import PostgreSQLAdapter
except ImportError:
    PostgreSQLAdapter = None

try:
    from .mysql import MySQLAdapter
except ImportError:
    MySQLAdapter = None

try:
    from .redis import RedisAdapter
except ImportError:
    RedisAdapter = None

try:
    from .mongodb import MongoDBAdapter
except ImportError:
    MongoDBAdapter = None

__all__ = [
    'DatabaseAdapter',
    'SQLiteAdapter',
    'PostgreSQLAdapter',
    'MySQLAdapter', 
    'RedisAdapter',
    'MongoDBAdapter'
]
