"""
SQLite Database Adapter.

SQLite adapter for WolfPy ORM.
"""

import sqlite3
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager
from .base import DatabaseAdapter


class SQLiteAdapter(DatabaseAdapter):
    """SQLite database adapter."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize SQLite adapter.
        
        Args:
            config: Configuration dictionary with 'database' key
        """
        super().__init__(config)
        self.database_path = config.get('database', 'wolfpy.db')
    
    def connect(self):
        """Establish SQLite connection."""
        self.connection = sqlite3.connect(self.database_path)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        
        # Enable foreign key constraints
        self.execute("PRAGMA foreign_keys = ON")
    
    def disconnect(self):
        """Close SQLite connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None
    
    def execute(self, sql: str, params: Tuple = ()) -> sqlite3.Cursor:
        """Execute SQL query."""
        if not self.connection:
            self.connect()
        return self.cursor.execute(sql, params)
    
    def fetchone(self, sql: str, params: Tuple = ()) -> Optional[Tuple]:
        """Execute query and fetch one result."""
        self.execute(sql, params)
        return self.cursor.fetchone()
    
    def fetchall(self, sql: str, params: Tuple = ()) -> List[Tuple]:
        """Execute query and fetch all results."""
        self.execute(sql, params)
        return self.cursor.fetchall()
    
    def commit(self):
        """Commit transaction."""
        if self.connection:
            self.connection.commit()
    
    def rollback(self):
        """Rollback transaction."""
        if self.connection:
            self.connection.rollback()
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        try:
            yield self
            self.commit()
        except Exception:
            self.rollback()
            raise
    
    def create_table(self, table_name: str, columns: List[str]):
        """Create table with given columns."""
        columns_sql = ', '.join(columns)
        sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_sql})"
        self.execute(sql)
        self.commit()
    
    def drop_table(self, table_name: str):
        """Drop table."""
        sql = f"DROP TABLE IF EXISTS {table_name}"
        self.execute(sql)
        self.commit()
    
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists."""
        sql = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        result = self.fetchone(sql, (table_name,))
        return result is not None
    
    def get_table_columns(self, table_name: str) -> List[str]:
        """Get list of column names for table."""
        sql = f"PRAGMA table_info({table_name})"
        rows = self.fetchall(sql)
        return [row[1] for row in rows]  # Column name is at index 1
    
    def format_sql_type(self, field_type: str) -> str:
        """Format field type for SQLite."""
        # SQLite type mapping
        type_mapping = {
            'DECIMAL': 'REAL',
            'DOUBLE': 'REAL',
            'FLOAT': 'REAL',
        }
        return type_mapping.get(field_type, field_type)
    
    def get_last_insert_id(self) -> Optional[int]:
        """Get the ID of the last inserted row."""
        if self.cursor:
            return self.cursor.lastrowid
        return None
    
    def create_index(self, table_name: str, column_names: List[str], unique: bool = False):
        """Create index on table columns."""
        index_name = f"idx_{table_name}_{'_'.join(column_names)}"
        unique_sql = "UNIQUE " if unique else ""
        columns_sql = ', '.join(column_names)
        sql = f"CREATE {unique_sql}INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns_sql})"
        self.execute(sql)
        self.commit()
    
    def drop_index(self, index_name: str):
        """Drop index."""
        sql = f"DROP INDEX IF EXISTS {index_name}"
        self.execute(sql)
        self.commit()
    
    def vacuum(self):
        """Vacuum database to reclaim space."""
        self.execute("VACUUM")
    
    def analyze(self):
        """Analyze database for query optimization."""
        self.execute("ANALYZE")
