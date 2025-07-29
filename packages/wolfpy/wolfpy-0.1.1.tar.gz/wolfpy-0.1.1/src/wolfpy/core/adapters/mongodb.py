"""
MongoDB Database Adapter.

MongoDB adapter for WolfPy ORM (NoSQL document store).
"""

from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager
from .base import DatabaseAdapter

try:
    import pymongo
    from bson import ObjectId
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False


class MongoDBAdapter(DatabaseAdapter):
    """MongoDB database adapter for document operations."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize MongoDB adapter.
        
        Args:
            config: Configuration dictionary with connection parameters
        """
        if not PYMONGO_AVAILABLE:
            raise ImportError("pymongo is required for MongoDB support. Install with: pip install pymongo")
        
        super().__init__(config)
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 27017)
        self.database_name = config.get('database', 'wolfpy')
        self.username = config.get('username', None)
        self.password = config.get('password', None)
        self.auth_source = config.get('auth_source', 'admin')
        
        self.client = None
        self.database = None
    
    def connect(self):
        """Establish MongoDB connection."""
        connection_string = f"mongodb://"
        
        if self.username and self.password:
            connection_string += f"{self.username}:{self.password}@"
        
        connection_string += f"{self.host}:{self.port}/"
        
        if self.username and self.password:
            connection_string += f"?authSource={self.auth_source}"
        
        self.client = pymongo.MongoClient(connection_string)
        self.database = self.client[self.database_name]
        
        # Test connection
        self.client.admin.command('ping')
    
    def disconnect(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
        self.client = None
        self.database = None
    
    def execute(self, operation: str, collection_name: str, *args, **kwargs) -> Any:
        """Execute MongoDB operation."""
        if not self.database:
            self.connect()
        
        collection = self.database[collection_name]
        method = getattr(collection, operation)
        return method(*args, **kwargs)
    
    def fetchone(self, collection_name: str, filter_dict: Dict = None) -> Optional[Dict]:
        """Find one document."""
        if not self.database:
            self.connect()
        
        collection = self.database[collection_name]
        return collection.find_one(filter_dict or {})
    
    def fetchall(self, collection_name: str, filter_dict: Dict = None) -> List[Dict]:
        """Find all documents matching filter."""
        if not self.database:
            self.connect()
        
        collection = self.database[collection_name]
        return list(collection.find(filter_dict or {}))
    
    def commit(self):
        """MongoDB operations are atomic by default."""
        pass
    
    def rollback(self):
        """MongoDB doesn't support traditional rollback."""
        pass
    
    @contextmanager
    def transaction(self):
        """Context manager for MongoDB transactions (requires replica set)."""
        if not self.client:
            self.connect()
        
        with self.client.start_session() as session:
            with session.start_transaction():
                try:
                    yield session
                except Exception:
                    # Transaction will be automatically aborted
                    raise
    
    def create_table(self, table_name: str, columns: List[str]):
        """Create collection (MongoDB equivalent of table)."""
        if not self.database:
            self.connect()
        
        # MongoDB creates collections automatically, but we can create explicitly
        self.database.create_collection(table_name)
        
        # Store schema information
        schema_doc = {
            '_id': f"schema_{table_name}",
            'collection': table_name,
            'columns': columns,
            'created_at': pymongo.datetime.datetime.utcnow()
        }
        self.database['_schemas'].insert_one(schema_doc)
    
    def drop_table(self, table_name: str):
        """Drop collection."""
        if not self.database:
            self.connect()
        
        self.database[table_name].drop()
        
        # Remove schema
        self.database['_schemas'].delete_one({'_id': f"schema_{table_name}"})
    
    def table_exists(self, table_name: str) -> bool:
        """Check if collection exists."""
        if not self.database:
            self.connect()
        
        return table_name in self.database.list_collection_names()
    
    def get_table_columns(self, table_name: str) -> List[str]:
        """Get list of column names for collection."""
        if not self.database:
            self.connect()
        
        schema_doc = self.database['_schemas'].find_one({'_id': f"schema_{table_name}"})
        if schema_doc:
            return schema_doc.get('columns', [])
        return []
    
    def supports_foreign_keys(self) -> bool:
        """MongoDB doesn't enforce foreign keys."""
        return False
    
    def supports_transactions(self) -> bool:
        """MongoDB supports transactions in replica sets."""
        return True
    
    # MongoDB-specific methods
    
    def insert_one(self, collection_name: str, document: Dict[str, Any]) -> Any:
        """Insert single document."""
        if not self.database:
            self.connect()
        
        collection = self.database[collection_name]
        return collection.insert_one(document)
    
    def insert_many(self, collection_name: str, documents: List[Dict[str, Any]]) -> Any:
        """Insert multiple documents."""
        if not self.database:
            self.connect()
        
        collection = self.database[collection_name]
        return collection.insert_many(documents)
    
    def find_one(self, collection_name: str, filter_dict: Dict = None, projection: Dict = None) -> Optional[Dict]:
        """Find one document with projection."""
        if not self.database:
            self.connect()
        
        collection = self.database[collection_name]
        return collection.find_one(filter_dict or {}, projection)
    
    def find(self, collection_name: str, filter_dict: Dict = None, projection: Dict = None, 
             sort: List[Tuple] = None, limit: int = None, skip: int = None) -> List[Dict]:
        """Find documents with advanced options."""
        if not self.database:
            self.connect()
        
        collection = self.database[collection_name]
        cursor = collection.find(filter_dict or {}, projection)
        
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        
        return list(cursor)
    
    def update_one(self, collection_name: str, filter_dict: Dict, update_dict: Dict) -> Any:
        """Update single document."""
        if not self.database:
            self.connect()
        
        collection = self.database[collection_name]
        return collection.update_one(filter_dict, update_dict)
    
    def update_many(self, collection_name: str, filter_dict: Dict, update_dict: Dict) -> Any:
        """Update multiple documents."""
        if not self.database:
            self.connect()
        
        collection = self.database[collection_name]
        return collection.update_many(filter_dict, update_dict)
    
    def delete_one(self, collection_name: str, filter_dict: Dict) -> Any:
        """Delete single document."""
        if not self.database:
            self.connect()
        
        collection = self.database[collection_name]
        return collection.delete_one(filter_dict)
    
    def delete_many(self, collection_name: str, filter_dict: Dict) -> Any:
        """Delete multiple documents."""
        if not self.database:
            self.connect()
        
        collection = self.database[collection_name]
        return collection.delete_many(filter_dict)
    
    def count_documents(self, collection_name: str, filter_dict: Dict = None) -> int:
        """Count documents matching filter."""
        if not self.database:
            self.connect()
        
        collection = self.database[collection_name]
        return collection.count_documents(filter_dict or {})
    
    def create_index(self, collection_name: str, keys: List[Tuple], unique: bool = False):
        """Create index on collection."""
        if not self.database:
            self.connect()
        
        collection = self.database[collection_name]
        return collection.create_index(keys, unique=unique)
    
    def drop_index(self, collection_name: str, index_name: str):
        """Drop index."""
        if not self.database:
            self.connect()
        
        collection = self.database[collection_name]
        return collection.drop_index(index_name)
