"""
Base Database Adapter.

Abstract base class for all database adapters.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Type
from contextlib import contextmanager


class DatabaseAdapter(ABC):
    """Abstract base class for database adapters."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize database adapter.
        
        Args:
            config: Database configuration dictionary
        """
        self.config = config
        self.connection = None
        self.cursor = None
    
    @abstractmethod
    def connect(self):
        """Establish database connection."""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Close database connection."""
        pass
    
    @abstractmethod
    def execute(self, sql: str, params: Tuple = ()) -> Any:
        """Execute SQL query."""
        pass
    
    @abstractmethod
    def fetchone(self, sql: str, params: Tuple = ()) -> Optional[Tuple]:
        """Execute query and fetch one result."""
        pass
    
    @abstractmethod
    def fetchall(self, sql: str, params: Tuple = ()) -> List[Tuple]:
        """Execute query and fetch all results."""
        pass
    
    @abstractmethod
    def commit(self):
        """Commit transaction."""
        pass
    
    @abstractmethod
    def rollback(self):
        """Rollback transaction."""
        pass
    
    @abstractmethod
    @contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        pass
    
    @abstractmethod
    def create_table(self, table_name: str, columns: List[str]):
        """Create table with given columns."""
        pass
    
    @abstractmethod
    def drop_table(self, table_name: str):
        """Drop table."""
        pass
    
    @abstractmethod
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists."""
        pass
    
    @abstractmethod
    def get_table_columns(self, table_name: str) -> List[str]:
        """Get list of column names for table."""
        pass
    
    def escape_identifier(self, identifier: str) -> str:
        """Escape database identifier (table/column name)."""
        return f'"{identifier}"'
    
    def format_sql_type(self, field_type: str) -> str:
        """Format field type for this database."""
        return field_type
    
    def supports_foreign_keys(self) -> bool:
        """Check if database supports foreign keys."""
        return True
    
    def supports_transactions(self) -> bool:
        """Check if database supports transactions."""
        return True
    
    def get_last_insert_id(self) -> Optional[int]:
        """Get the ID of the last inserted row."""
        return None
