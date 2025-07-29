"""
PostgreSQL Database Adapter.

PostgreSQL adapter for WolfPy ORM.
"""

from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager
from .base import DatabaseAdapter

try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL database adapter."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize PostgreSQL adapter.
        
        Args:
            config: Configuration dictionary with connection parameters
        """
        if not PSYCOPG2_AVAILABLE:
            raise ImportError("psycopg2 is required for PostgreSQL support. Install with: pip install psycopg2-binary")
        
        super().__init__(config)
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 5432)
        self.database = config.get('database', 'wolfpy')
        self.user = config.get('user', 'postgres')
        self.password = config.get('password', '')
    
    def connect(self):
        """Establish PostgreSQL connection."""
        self.connection = psycopg2.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password
        )
        self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    def disconnect(self):
        """Close PostgreSQL connection."""
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
        sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_sql})"
        self.execute(sql)
        self.commit()
    
    def drop_table(self, table_name: str):
        """Drop table."""
        sql = f"DROP TABLE IF EXISTS {table_name} CASCADE"
        self.execute(sql)
        self.commit()
    
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists."""
        sql = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = %s
        )
        """
        result = self.fetchone(sql, (table_name,))
        return result[0] if result else False
    
    def get_table_columns(self, table_name: str) -> List[str]:
        """Get list of column names for table."""
        sql = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = %s
        ORDER BY ordinal_position
        """
        rows = self.fetchall(sql, (table_name,))
        return [row[0] for row in rows]
    
    def format_sql_type(self, field_type: str) -> str:
        """Format field type for PostgreSQL."""
        # PostgreSQL type mapping
        type_mapping = {
            'INTEGER': 'INTEGER',
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
        """Escape PostgreSQL identifier."""
        return f'"{identifier}"'
    
    def get_last_insert_id(self) -> Optional[int]:
        """Get the ID of the last inserted row."""
        # PostgreSQL uses RETURNING clause or sequences
        return None
    
    def create_sequence(self, sequence_name: str):
        """Create sequence for auto-increment fields."""
        sql = f"CREATE SEQUENCE IF NOT EXISTS {sequence_name}"
        self.execute(sql)
        self.commit()
    
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
