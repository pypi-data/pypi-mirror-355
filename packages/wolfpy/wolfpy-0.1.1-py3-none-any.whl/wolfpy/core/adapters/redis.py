"""
Redis Database Adapter.

Redis adapter for WolfPy ORM (NoSQL key-value store).
"""

import json
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager
from .base import DatabaseAdapter

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class RedisAdapter(DatabaseAdapter):
    """Redis database adapter for key-value operations."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Redis adapter.
        
        Args:
            config: Configuration dictionary with connection parameters
        """
        if not REDIS_AVAILABLE:
            raise ImportError("redis is required for Redis support. Install with: pip install redis")
        
        super().__init__(config)
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 6379)
        self.db = config.get('db', 0)
        self.password = config.get('password', None)
        self.decode_responses = config.get('decode_responses', True)
    
    def connect(self):
        """Establish Redis connection."""
        self.connection = redis.Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            decode_responses=self.decode_responses
        )
        # Test connection
        self.connection.ping()
    
    def disconnect(self):
        """Close Redis connection."""
        if self.connection:
            self.connection.close()
        self.connection = None
    
    def execute(self, command: str, *args) -> Any:
        """Execute Redis command."""
        if not self.connection:
            self.connect()
        return self.connection.execute_command(command, *args)
    
    def fetchone(self, key: str, params: Tuple = ()) -> Optional[Any]:
        """Get single value by key."""
        if not self.connection:
            self.connect()
        value = self.connection.get(key)
        if value and isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value
    
    def fetchall(self, pattern: str = "*", params: Tuple = ()) -> List[Tuple]:
        """Get all keys matching pattern."""
        if not self.connection:
            self.connect()
        keys = self.connection.keys(pattern)
        results = []
        for key in keys:
            value = self.fetchone(key)
            results.append((key, value))
        return results
    
    def commit(self):
        """Redis doesn't need explicit commits."""
        pass
    
    def rollback(self):
        """Redis doesn't support transactions in the traditional sense."""
        pass
    
    @contextmanager
    def transaction(self):
        """Context manager for Redis pipeline (batch operations)."""
        if not self.connection:
            self.connect()
        
        pipe = self.connection.pipeline()
        try:
            yield pipe
            pipe.execute()
        except Exception:
            # Redis pipeline doesn't support rollback
            raise
    
    def create_table(self, table_name: str, columns: List[str]):
        """Redis doesn't have tables, but we can create a namespace."""
        # Store table schema in Redis
        schema_key = f"schema:{table_name}"
        schema = {
            'columns': columns,
            'created_at': self.connection.time()[0]
        }
        self.connection.set(schema_key, json.dumps(schema))
    
    def drop_table(self, table_name: str):
        """Drop all keys for a table namespace."""
        pattern = f"{table_name}:*"
        keys = self.connection.keys(pattern)
        if keys:
            self.connection.delete(*keys)
        
        # Remove schema
        schema_key = f"schema:{table_name}"
        self.connection.delete(schema_key)
    
    def table_exists(self, table_name: str) -> bool:
        """Check if table schema exists."""
        schema_key = f"schema:{table_name}"
        return self.connection.exists(schema_key) > 0
    
    def get_table_columns(self, table_name: str) -> List[str]:
        """Get list of column names for table."""
        schema_key = f"schema:{table_name}"
        schema_data = self.connection.get(schema_key)
        if schema_data:
            schema = json.loads(schema_data)
            return schema.get('columns', [])
        return []
    
    def supports_foreign_keys(self) -> bool:
        """Redis doesn't support foreign keys."""
        return False
    
    def supports_transactions(self) -> bool:
        """Redis supports pipeline operations."""
        return True
    
    # Redis-specific methods
    
    def set(self, key: str, value: Any, ex: Optional[int] = None):
        """Set key-value pair with optional expiration."""
        if not self.connection:
            self.connect()
        
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        return self.connection.set(key, value, ex=ex)
    
    def get(self, key: str) -> Any:
        """Get value by key."""
        return self.fetchone(key)
    
    def delete(self, *keys: str) -> int:
        """Delete keys."""
        if not self.connection:
            self.connect()
        return self.connection.delete(*keys)
    
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        if not self.connection:
            self.connect()
        return self.connection.exists(key) > 0
    
    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for key."""
        if not self.connection:
            self.connect()
        return self.connection.expire(key, seconds)
    
    def ttl(self, key: str) -> int:
        """Get time to live for key."""
        if not self.connection:
            self.connect()
        return self.connection.ttl(key)
    
    def incr(self, key: str, amount: int = 1) -> int:
        """Increment key value."""
        if not self.connection:
            self.connect()
        return self.connection.incr(key, amount)
    
    def decr(self, key: str, amount: int = 1) -> int:
        """Decrement key value."""
        if not self.connection:
            self.connect()
        return self.connection.decr(key, amount)
    
    def hset(self, name: str, mapping: Dict[str, Any]) -> int:
        """Set hash fields."""
        if not self.connection:
            self.connect()
        
        # Convert complex values to JSON
        json_mapping = {}
        for key, value in mapping.items():
            if isinstance(value, (dict, list)):
                json_mapping[key] = json.dumps(value)
            else:
                json_mapping[key] = value
        
        return self.connection.hset(name, mapping=json_mapping)
    
    def hget(self, name: str, key: str) -> Any:
        """Get hash field value."""
        if not self.connection:
            self.connect()
        
        value = self.connection.hget(name, key)
        if value and isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value
    
    def hgetall(self, name: str) -> Dict[str, Any]:
        """Get all hash fields."""
        if not self.connection:
            self.connect()
        
        data = self.connection.hgetall(name)
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                try:
                    result[key] = json.loads(value)
                except json.JSONDecodeError:
                    result[key] = value
            else:
                result[key] = value
        return result
