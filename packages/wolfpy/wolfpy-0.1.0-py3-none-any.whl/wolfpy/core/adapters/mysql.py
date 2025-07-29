"""
MySQL Database Adapter.

MySQL adapter for WolfPy ORM.
"""

from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager
from .base import DatabaseAdapter

try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False


class MySQLAdapter(DatabaseAdapter):
    """MySQL database adapter."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize MySQL adapter.
        
        Args:
            config: Configuration dictionary with connection parameters
        """
        if not MYSQL_AVAILABLE:
            raise ImportError("mysql-connector-python is required for MySQL support. Install with: pip install mysql-connector-python")
        
        super().__init__(config)
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 3306)
        self.database = config.get('database', 'wolfpy')
        self.user = config.get('user', 'root')
        self.password = config.get('password', '')
    
    def connect(self):
        """Establish MySQL connection."""
        self.connection = mysql.connector.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
            autocommit=False
        )
        self.cursor = self.connection.cursor(dictionary=True)
    
    def disconnect(self):
        """Close MySQL connection."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        self.connection = None
        self.cursor = None
    
    def execute(self, sql: str, params: Tuple = ()) -> Any:
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
        sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_sql}) ENGINE=InnoDB"
        self.execute(sql)
        self.commit()
    
    def drop_table(self, table_name: str):
        """Drop table."""
        sql = f"DROP TABLE IF EXISTS {table_name}"
        self.execute(sql)
        self.commit()
    
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists."""
        sql = """
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_schema = DATABASE() 
        AND table_name = %s
        """
        result = self.fetchone(sql, (table_name,))
        return result[0] > 0 if result else False
    
    def get_table_columns(self, table_name: str) -> List[str]:
        """Get list of column names for table."""
        sql = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = DATABASE() 
        AND table_name = %s
        ORDER BY ordinal_position
        """
        rows = self.fetchall(sql, (table_name,))
        return [row['column_name'] for row in rows]
    
    def format_sql_type(self, field_type: str) -> str:
        """Format field type for MySQL."""
        # MySQL type mapping
        type_mapping = {
            'INTEGER': 'INT',
            'VARCHAR': 'VARCHAR',
            'TEXT': 'TEXT',
            'BOOLEAN': 'BOOLEAN',
            'DECIMAL': 'DECIMAL',
            'TIMESTAMP': 'TIMESTAMP',
            'DATE': 'DATE',
            'TIME': 'TIME',
        }
        return type_mapping.get(field_type, field_type)
    
    def escape_identifier(self, identifier: str) -> str:
        """Escape MySQL identifier."""
        return f"`{identifier}`"
    
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
        sql = f"CREATE {unique_sql}INDEX {index_name} ON {table_name} ({columns_sql})"
        self.execute(sql)
        self.commit()
    
    def drop_index(self, table_name: str, index_name: str):
        """Drop index."""
        sql = f"DROP INDEX {index_name} ON {table_name}"
        self.execute(sql)
        self.commit()
    
    def show_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Show indexes for table."""
        sql = f"SHOW INDEX FROM {table_name}"
        return self.fetchall(sql)
