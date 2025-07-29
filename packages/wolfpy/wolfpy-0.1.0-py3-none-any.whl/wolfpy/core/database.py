"""
WolfPy Database Module.

This module provides ORM and database functionality for WolfPy applications.
Includes a comprehensive ORM with model definitions, queries, migrations, and multi-database support.
"""

import sqlite3
import json
import os
import re
import hashlib
import time
import threading
import weakref
from typing import Dict, List, Any, Optional, Type, Union, Tuple, Set, Callable
from datetime import datetime
from contextlib import contextmanager
from abc import ABC, abstractmethod
from collections import defaultdict, OrderedDict
from dataclasses import dataclass, field
from enum import Enum


class Field:
    """Base class for database fields."""
    
    def __init__(self, 
                 primary_key: bool = False,
                 nullable: bool = True,
                 default: Any = None,
                 unique: bool = False):
        """
        Initialize a field.
        
        Args:
            primary_key: Whether this is a primary key
            nullable: Whether field can be NULL
            default: Default value
            unique: Whether field must be unique
        """
        self.primary_key = primary_key
        self.nullable = nullable
        self.default = default
        self.unique = unique
        self.name = None  # Set by metaclass
    
    def to_sql_type(self) -> str:
        """Convert field to SQL type."""
        raise NotImplementedError
    
    def to_python(self, value: Any) -> Any:
        """Convert database value to Python value."""
        return value
    
    def to_db(self, value: Any) -> Any:
        """Convert Python value to database value."""
        return value


class IntegerField(Field):
    """Integer field."""
    
    def to_sql_type(self) -> str:
        return "INTEGER"
    
    def to_python(self, value: Any) -> Optional[int]:
        if value is None:
            return None
        return int(value)


class StringField(Field):
    """String field."""
    
    def __init__(self, max_length: int = 255, **kwargs):
        """
        Initialize string field.
        
        Args:
            max_length: Maximum string length
            **kwargs: Other field options
        """
        super().__init__(**kwargs)
        self.max_length = max_length
    
    def to_sql_type(self) -> str:
        return f"VARCHAR({self.max_length})"
    
    def to_python(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        return str(value)


class TextField(Field):
    """Text field for long strings."""
    
    def to_sql_type(self) -> str:
        return "TEXT"
    
    def to_python(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        return str(value)


class BooleanField(Field):
    """Boolean field."""
    
    def to_sql_type(self) -> str:
        return "BOOLEAN"
    
    def to_python(self, value: Any) -> Optional[bool]:
        if value is None:
            return None
        return bool(value)
    
    def to_db(self, value: Any) -> Any:
        if value is None:
            return None
        return 1 if value else 0


class DateTimeField(Field):
    """DateTime field."""
    
    def __init__(self, auto_now: bool = False, auto_now_add: bool = False, **kwargs):
        """
        Initialize datetime field.
        
        Args:
            auto_now: Automatically update on save
            auto_now_add: Automatically set on creation
            **kwargs: Other field options
        """
        super().__init__(**kwargs)
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add
    
    def to_sql_type(self) -> str:
        return "TIMESTAMP"
    
    def to_python(self, value: Any) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(value)
    
    def to_db(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return value


class JSONField(Field):
    """JSON field."""

    def to_sql_type(self) -> str:
        return "TEXT"

    def to_python(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, str):
            return json.loads(value)
        return value

    def to_db(self, value: Any) -> Any:
        if value is None:
            return None
        return json.dumps(value)


class ForeignKeyField(Field):
    """Foreign key field for model relationships."""

    def __init__(self, to_model: Union[str, Type['Model']], on_delete: str = 'CASCADE',
                 related_name: str = None, **kwargs):
        """
        Initialize foreign key field.

        Args:
            to_model: Target model class or string reference
            on_delete: What to do when referenced object is deleted
            related_name: Name for reverse relationship
            **kwargs: Other field options
        """
        super().__init__(**kwargs)
        self.to_model = to_model
        self.on_delete = on_delete
        self.related_name = related_name

    def to_sql_type(self) -> str:
        return "INTEGER"

    def get_foreign_key_constraint(self, table_name: str) -> str:
        """Generate foreign key constraint SQL."""
        if isinstance(self.to_model, str):
            target_table = self.to_model.lower()
        else:
            target_table = self.to_model.get_table_name()

        return f"FOREIGN KEY ({self.name}) REFERENCES {target_table}(id) ON DELETE {self.on_delete}"


class ManyToManyField(Field):
    """Many-to-many relationship field."""

    def __init__(self, to_model: Union[str, Type['Model']], through: str = None,
                 related_name: str = None, **kwargs):
        """
        Initialize many-to-many field.

        Args:
            to_model: Target model class or string reference
            through: Custom through table name
            related_name: Name for reverse relationship
            **kwargs: Other field options
        """
        super().__init__(**kwargs)
        self.to_model = to_model
        self.through = through
        self.related_name = related_name

    def to_sql_type(self) -> str:
        # M2M fields don't have a direct SQL representation
        return None

    def get_through_table_name(self, source_model: str) -> str:
        """Get the through table name."""
        if self.through:
            return self.through

        if isinstance(self.to_model, str):
            target_model = self.to_model.lower()
        else:
            target_model = self.to_model.get_table_name()

        # Create alphabetically ordered table name
        tables = sorted([source_model.lower(), target_model])
        return f"{tables[0]}_{tables[1]}"


class OneToOneField(ForeignKeyField):
    """One-to-one relationship field."""

    def __init__(self, to_model: Union[str, Type['Model']], **kwargs):
        """Initialize one-to-one field."""
        kwargs['unique'] = True  # One-to-one requires unique constraint
        super().__init__(to_model, **kwargs)


class EmailField(StringField):
    """Email field with validation."""

    def __init__(self, **kwargs):
        kwargs.setdefault('max_length', 254)
        super().__init__(**kwargs)

    def validate(self, value: str) -> bool:
        """Validate email format."""
        if value is None:
            return self.nullable

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, value))


class URLField(StringField):
    """URL field with validation."""

    def __init__(self, **kwargs):
        kwargs.setdefault('max_length', 2048)
        super().__init__(**kwargs)

    def validate(self, value: str) -> bool:
        """Validate URL format."""
        if value is None:
            return self.nullable

        url_pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?$'
        return bool(re.match(url_pattern, value))


class DecimalField(Field):
    """Decimal field for precise numeric values."""

    def __init__(self, max_digits: int = 10, decimal_places: int = 2, **kwargs):
        """
        Initialize decimal field.

        Args:
            max_digits: Maximum number of digits
            decimal_places: Number of decimal places
            **kwargs: Other field options
        """
        super().__init__(**kwargs)
        self.max_digits = max_digits
        self.decimal_places = decimal_places

    def to_sql_type(self) -> str:
        return f"DECIMAL({self.max_digits}, {self.decimal_places})"

    def to_python(self, value: Any) -> Optional[float]:
        if value is None:
            return None
        return float(value)


class QueryOperator(Enum):
    """Query operators for filtering."""
    EQUALS = "="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN = "<"
    LESS_THAN_OR_EQUAL = "<="
    LIKE = "LIKE"
    ILIKE = "ILIKE"
    IN = "IN"
    NOT_IN = "NOT IN"
    IS_NULL = "IS NULL"
    IS_NOT_NULL = "IS NOT NULL"
    BETWEEN = "BETWEEN"


@dataclass
class QueryFilter:
    """Represents a query filter condition."""
    field: str
    operator: QueryOperator
    value: Any = None

    def to_sql(self) -> Tuple[str, List[Any]]:
        """Convert filter to SQL WHERE clause."""
        if self.operator == QueryOperator.IS_NULL:
            return f"{self.field} IS NULL", []
        elif self.operator == QueryOperator.IS_NOT_NULL:
            return f"{self.field} IS NOT NULL", []
        elif self.operator == QueryOperator.IN:
            if not isinstance(self.value, (list, tuple)):
                raise ValueError("IN operator requires list or tuple value")
            placeholders = ",".join("?" * len(self.value))
            return f"{self.field} IN ({placeholders})", list(self.value)
        elif self.operator == QueryOperator.NOT_IN:
            if not isinstance(self.value, (list, tuple)):
                raise ValueError("NOT IN operator requires list or tuple value")
            placeholders = ",".join("?" * len(self.value))
            return f"{self.field} NOT IN ({placeholders})", list(self.value)
        elif self.operator == QueryOperator.BETWEEN:
            if not isinstance(self.value, (list, tuple)) or len(self.value) != 2:
                raise ValueError("BETWEEN operator requires list/tuple with 2 values")
            return f"{self.field} BETWEEN ? AND ?", list(self.value)
        else:
            return f"{self.field} {self.operator.value} ?", [self.value]


@dataclass
class QueryJoin:
    """Represents a query join."""
    table: str
    on_condition: str
    join_type: str = "INNER"

    def to_sql(self) -> str:
        """Convert join to SQL."""
        return f"{self.join_type} JOIN {self.table} ON {self.on_condition}"


@dataclass
class QueryOrder:
    """Represents query ordering."""
    field: str
    direction: str = "ASC"

    def to_sql(self) -> str:
        """Convert order to SQL."""
        return f"{self.field} {self.direction.upper()}"


class QuerySet:
    """Advanced query builder for database operations."""

    def __init__(self, model_class: Type['Model'], db: 'Database'):
        """
        Initialize QuerySet.

        Args:
            model_class: Model class to query
            db: Database instance
        """
        self.model_class = model_class
        self.db = db
        self.filters: List[QueryFilter] = []
        self.joins: List[QueryJoin] = []
        self._order_by: List[QueryOrder] = []
        self.limit_count: Optional[int] = None
        self.offset_count: Optional[int] = None
        self.select_fields: Optional[List[str]] = None
        self.distinct_fields: Optional[List[str]] = None
        self._cache: Optional[List['Model']] = None
        self._cache_key: Optional[str] = None

    def filter(self, **kwargs) -> 'QuerySet':
        """Add filter conditions."""
        new_qs = self._clone()

        for field, value in kwargs.items():
            # Parse field lookups (e.g., 'name__icontains', 'age__gt')
            if '__' in field:
                field_name, lookup = field.rsplit('__', 1)
                operator = self._lookup_to_operator(lookup)

                # Handle special LIKE cases that need value modification
                if lookup == 'contains':
                    value = f"%{value}%"
                elif lookup == 'icontains':
                    value = f"%{value}%"
                elif lookup == 'startswith':
                    value = f"{value}%"
                elif lookup == 'endswith':
                    value = f"%{value}"
            else:
                field_name = field
                operator = QueryOperator.EQUALS

            new_qs.filters.append(QueryFilter(field_name, operator, value))

        return new_qs

    def exclude(self, **kwargs) -> 'QuerySet':
        """Exclude records matching conditions."""
        new_qs = self._clone()

        for field, value in kwargs.items():
            if '__' in field:
                field_name, lookup = field.rsplit('__', 1)
                operator = self._lookup_to_operator(lookup)
            else:
                field_name = field
                operator = QueryOperator.NOT_EQUALS

            new_qs.filters.append(QueryFilter(field_name, operator, value))

        return new_qs

    def order_by(self, *fields) -> 'QuerySet':
        """Add ordering to query."""
        new_qs = self._clone()
        new_qs._order_by = []

        for field in fields:
            if field.startswith('-'):
                new_qs._order_by.append(QueryOrder(field[1:], "DESC"))
            else:
                new_qs._order_by.append(QueryOrder(field, "ASC"))

        return new_qs

    def limit(self, count: int) -> 'QuerySet':
        """Limit number of results."""
        new_qs = self._clone()
        new_qs.limit_count = count
        return new_qs

    def offset(self, count: int) -> 'QuerySet':
        """Add offset to query."""
        new_qs = self._clone()
        new_qs.offset_count = count
        return new_qs

    def select_related(self, *fields) -> 'QuerySet':
        """Select related objects in a single query (JOIN)."""
        new_qs = self._clone()

        for field in fields:
            # Add JOIN for foreign key relationships
            if field in self.model_class._foreign_keys:
                fk_field = self.model_class._foreign_keys[field]
                if isinstance(fk_field.to_model, str):
                    target_table = fk_field.to_model.lower()
                else:
                    target_table = fk_field.to_model.get_table_name()

                join = QueryJoin(
                    table=target_table,
                    on_condition=f"{self.model_class.get_table_name()}.{field} = {target_table}.id"
                )
                new_qs.joins.append(join)

        return new_qs

    def distinct(self, *fields) -> 'QuerySet':
        """Add DISTINCT to query."""
        new_qs = self._clone()
        new_qs.distinct_fields = list(fields) if fields else ['*']
        return new_qs

    def values(self, *fields) -> 'QuerySet':
        """Return dictionaries instead of model instances."""
        new_qs = self._clone()
        new_qs.select_fields = list(fields)
        return new_qs

    def all(self) -> List['Model']:
        """Get all results."""
        return list(self)

    def first(self) -> Optional['Model']:
        """Get first result."""
        results = self.limit(1).all()
        return results[0] if results else None

    def last(self) -> Optional['Model']:
        """Get last result."""
        # Reverse order and get first
        reversed_order = []
        for order in self._order_by:
            direction = "ASC" if order.direction == "DESC" else "DESC"
            reversed_order.append(QueryOrder(order.field, direction))

        new_qs = self._clone()
        new_qs._order_by = reversed_order
        results = new_qs.limit(1).all()
        return results[0] if results else None

    def get(self, **kwargs) -> 'Model':
        """Get single object matching criteria."""
        qs = self.filter(**kwargs)
        results = qs.all()

        if not results:
            raise ValueError(f"No {self.model_class.__name__} found matching criteria")
        elif len(results) > 1:
            raise ValueError(f"Multiple {self.model_class.__name__} found matching criteria")

        return results[0]

    def count(self) -> int:
        """Get count of results."""
        sql, params = self._build_count_sql()
        cursor = self.db.execute(sql, params)
        return cursor.fetchone()[0]

    def exists(self) -> bool:
        """Check if any results exist."""
        return self.count() > 0

    def delete(self) -> int:
        """Delete all matching records."""
        sql, params = self._build_delete_sql()
        cursor = self.db.execute(sql, params)
        return cursor.rowcount

    def update(self, **kwargs) -> int:
        """Update all matching records."""
        if not kwargs:
            return 0

        sql, params = self._build_update_sql(kwargs)
        cursor = self.db.execute(sql, params)
        return cursor.rowcount

    def aggregate(self, **kwargs) -> Dict[str, Any]:
        """Perform aggregation operations."""
        sql, params = self._build_aggregate_sql(kwargs)
        cursor = self.db.execute(sql, params)
        result = cursor.fetchone()

        return dict(zip(kwargs.keys(), result))

    def _clone(self) -> 'QuerySet':
        """Create a copy of this QuerySet."""
        new_qs = QuerySet(self.model_class, self.db)
        new_qs.filters = self.filters.copy()
        new_qs.joins = self.joins.copy()
        new_qs._order_by = self._order_by.copy()
        new_qs.limit_count = self.limit_count
        new_qs.offset_count = self.offset_count
        new_qs.select_fields = self.select_fields
        new_qs.distinct_fields = self.distinct_fields
        return new_qs

    def _lookup_to_operator(self, lookup: str) -> QueryOperator:
        """Convert field lookup to operator."""
        lookup_map = {
            'exact': QueryOperator.EQUALS,
            'iexact': QueryOperator.EQUALS,  # Case-insensitive exact (would need LOWER())
            'contains': QueryOperator.LIKE,
            'icontains': QueryOperator.ILIKE,
            'gt': QueryOperator.GREATER_THAN,
            'gte': QueryOperator.GREATER_THAN_OR_EQUAL,
            'lt': QueryOperator.LESS_THAN,
            'lte': QueryOperator.LESS_THAN_OR_EQUAL,
            'in': QueryOperator.IN,
            'isnull': QueryOperator.IS_NULL,
            'startswith': QueryOperator.LIKE,
            'endswith': QueryOperator.LIKE,
        }

        return lookup_map.get(lookup, QueryOperator.EQUALS)

    def _build_sql(self) -> Tuple[str, List[Any]]:
        """Build complete SQL query."""
        # SELECT clause
        if self.select_fields:
            select_clause = f"SELECT {', '.join(self.select_fields)}"
        elif self.distinct_fields:
            if self.distinct_fields == ['*']:
                select_clause = "SELECT DISTINCT *"
            else:
                select_clause = f"SELECT DISTINCT {', '.join(self.distinct_fields)}"
        else:
            select_clause = "SELECT *"

        # FROM clause
        from_clause = f"FROM {self.model_class.get_table_name()}"

        # JOIN clauses
        join_clauses = []
        for join in self.joins:
            join_clauses.append(join.to_sql())

        # WHERE clause
        where_clauses = []
        params = []

        for filter_obj in self.filters:
            clause, filter_params = filter_obj.to_sql()
            where_clauses.append(clause)
            params.extend(filter_params)

        where_clause = ""
        if where_clauses:
            where_clause = f"WHERE {' AND '.join(where_clauses)}"

        # ORDER BY clause
        order_clause = ""
        if self._order_by:
            order_parts = [order.to_sql() for order in self._order_by]
            order_clause = f"ORDER BY {', '.join(order_parts)}"

        # LIMIT and OFFSET
        limit_clause = ""
        if self.limit_count is not None:
            limit_clause = f"LIMIT {self.limit_count}"
            if self.offset_count is not None:
                limit_clause += f" OFFSET {self.offset_count}"

        # Combine all parts
        sql_parts = [select_clause, from_clause]
        sql_parts.extend(join_clauses)
        if where_clause:
            sql_parts.append(where_clause)
        if order_clause:
            sql_parts.append(order_clause)
        if limit_clause:
            sql_parts.append(limit_clause)

        return " ".join(sql_parts), params

    def _build_count_sql(self) -> Tuple[str, List[Any]]:
        """Build SQL for counting results."""
        # WHERE clause
        where_clauses = []
        params = []

        for filter_obj in self.filters:
            clause, filter_params = filter_obj.to_sql()
            where_clauses.append(clause)
            params.extend(filter_params)

        where_clause = ""
        if where_clauses:
            where_clause = f"WHERE {' AND '.join(where_clauses)}"

        sql = f"SELECT COUNT(*) FROM {self.model_class.get_table_name()}"
        if where_clause:
            sql += f" {where_clause}"

        return sql, params

    def _build_delete_sql(self) -> Tuple[str, List[Any]]:
        """Build SQL for deleting results."""
        where_clauses = []
        params = []

        for filter_obj in self.filters:
            clause, filter_params = filter_obj.to_sql()
            where_clauses.append(clause)
            params.extend(filter_params)

        sql = f"DELETE FROM {self.model_class.get_table_name()}"
        if where_clauses:
            sql += f" WHERE {' AND '.join(where_clauses)}"

        return sql, params

    def _build_update_sql(self, updates: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """Build SQL for updating results."""
        set_clauses = []
        params = []

        # SET clause
        for field, value in updates.items():
            set_clauses.append(f"{field} = ?")
            params.append(value)

        # WHERE clause
        where_clauses = []
        for filter_obj in self.filters:
            clause, filter_params = filter_obj.to_sql()
            where_clauses.append(clause)
            params.extend(filter_params)

        sql = f"UPDATE {self.model_class.get_table_name()} SET {', '.join(set_clauses)}"
        if where_clauses:
            sql += f" WHERE {' AND '.join(where_clauses)}"

        return sql, params

    def _build_aggregate_sql(self, aggregates: Dict[str, str]) -> Tuple[str, List[Any]]:
        """Build SQL for aggregation."""
        select_parts = []

        for alias, expression in aggregates.items():
            # Parse aggregation expressions like 'count', 'sum__price', 'avg__rating'
            if '__' in expression:
                func, field = expression.split('__', 1)
                select_parts.append(f"{func.upper()}({field}) AS {alias}")
            else:
                # Simple count
                select_parts.append(f"COUNT(*) AS {alias}")

        # WHERE clause
        where_clauses = []
        params = []

        for filter_obj in self.filters:
            clause, filter_params = filter_obj.to_sql()
            where_clauses.append(clause)
            params.extend(filter_params)

        sql = f"SELECT {', '.join(select_parts)} FROM {self.model_class.get_table_name()}"
        if where_clauses:
            sql += f" WHERE {' AND '.join(where_clauses)}"

        return sql, params

    def __iter__(self):
        """Make QuerySet iterable."""
        if self._cache is None:
            self._execute_query()
        return iter(self._cache)

    def __len__(self):
        """Get length of QuerySet."""
        if self._cache is None:
            self._execute_query()
        return len(self._cache)

    def __getitem__(self, key):
        """Support indexing and slicing."""
        if isinstance(key, slice):
            # Handle slicing
            start, stop, step = key.indices(len(self))
            if step != 1:
                raise ValueError("QuerySet slicing with step is not supported")

            new_qs = self._clone()
            new_qs.offset_count = start
            new_qs.limit_count = stop - start
            return new_qs
        else:
            # Handle indexing
            if self._cache is None:
                self._execute_query()
            return self._cache[key]

    def _execute_query(self):
        """Execute the query and cache results."""
        sql, params = self._build_sql()
        cursor = self.db.execute(sql, params)

        if self.select_fields:
            # Return dictionaries
            columns = [desc[0] for desc in cursor.description]
            self._cache = []
            for row in cursor.fetchall():
                self._cache.append(dict(zip(columns, row)))
        else:
            # Return model instances
            self._cache = []
            for row in cursor.fetchall():
                instance = self.model_class()

                # Map row data to model fields
                for i, field_name in enumerate(self.model_class._fields.keys()):
                    if i < len(row):
                        field = self.model_class._fields[field_name]
                        value = field.to_python(row[i])
                        instance._data[field_name] = value
                        instance._original_data[field_name] = value

                self._cache.append(instance)


class ModelMeta(type):
    """Metaclass for database models."""

    def __new__(cls, name, bases, attrs):
        # Collect fields
        fields = {}
        foreign_keys = {}
        many_to_many_fields = {}

        for key, value in list(attrs.items()):
            if isinstance(value, Field):
                value.name = key
                fields[key] = value

                # Track foreign keys for relationship setup
                if isinstance(value, ForeignKeyField):
                    foreign_keys[key] = value
                elif isinstance(value, ManyToManyField):
                    many_to_many_fields[key] = value

                # Don't remove M2M fields as they need special handling
                if not isinstance(value, ManyToManyField):
                    attrs.pop(key)

        # Add fields to class
        attrs['_fields'] = fields
        attrs['_foreign_keys'] = foreign_keys
        attrs['_many_to_many_fields'] = many_to_many_fields
        attrs['_table_name'] = attrs.get('_table_name', name.lower())
        attrs['_indexes'] = attrs.get('_indexes', [])
        attrs['_constraints'] = attrs.get('_constraints', [])

        return super().__new__(cls, name, bases, attrs)


class ModelManager:
    """Manager for model queries."""

    def __init__(self, model_class: Type['Model']):
        """Initialize manager."""
        self.model_class = model_class

    def get_queryset(self, db: 'Database' = None) -> QuerySet:
        """Get a QuerySet for this model."""
        if db is None:
            db = Database.get_default()
        return QuerySet(self.model_class, db)

    def all(self, db: 'Database' = None) -> QuerySet:
        """Get all objects."""
        return self.get_queryset(db)

    def filter(self, db: 'Database' = None, **kwargs) -> QuerySet:
        """Filter objects."""
        return self.get_queryset(db).filter(**kwargs)

    def exclude(self, db: 'Database' = None, **kwargs) -> QuerySet:
        """Exclude objects."""
        return self.get_queryset(db).exclude(**kwargs)

    def get(self, db: 'Database' = None, **kwargs) -> 'Model':
        """Get single object."""
        return self.get_queryset(db).get(**kwargs)

    def create(self, db: 'Database' = None, **kwargs) -> 'Model':
        """Create and save new object."""
        instance = self.model_class(**kwargs)
        instance.save(db)
        return instance

    def bulk_create(self, objects: List['Model'], db: 'Database' = None) -> List['Model']:
        """Create multiple objects efficiently."""
        if db is None:
            db = Database.get_default()

        for obj in objects:
            obj.save(db)

        return objects

    def count(self, db: 'Database' = None) -> int:
        """Count all objects."""
        return self.get_queryset(db).count()

    def exists(self, db: 'Database' = None) -> bool:
        """Check if any objects exist."""
        return self.get_queryset(db).exists()


class Model(metaclass=ModelMeta):
    """Base model class for database objects."""

    objects = None  # Will be set by metaclass

    def __init__(self, **kwargs):
        """Initialize model instance."""
        self._data = {}
        self._original_data = {}

        # Set field values
        for field_name, field in self._fields.items():
            if field_name in kwargs:
                value = kwargs[field_name]
            elif field.default is not None:
                value = field.default() if callable(field.default) else field.default
            else:
                value = None

            self._data[field_name] = value
            self._original_data[field_name] = value

    def __init_subclass__(cls, **kwargs):
        """Set up manager when subclass is created."""
        super().__init_subclass__(**kwargs)
        cls.objects = ModelManager(cls)
    
    def __getattr__(self, name: str) -> Any:
        """Get field value."""
        if name in self._fields:
            return self._data.get(name)
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")
    
    def __setattr__(self, name: str, value: Any):
        """Set field value."""
        if name.startswith('_') or name not in getattr(self, '_fields', {}):
            super().__setattr__(name, value)
        else:
            self._data[name] = value

    def validate(self) -> Dict[str, List[str]]:
        """
        Validate model instance.

        Returns:
            Dictionary of field names to list of error messages
        """
        errors = {}

        for field_name, field in self._fields.items():
            value = self._data.get(field_name)
            field_errors = []

            # Check nullable constraint
            if not field.nullable and value is None:
                field_errors.append(f"{field_name} cannot be null")

            # Check field-specific validation
            if hasattr(field, 'validate') and value is not None:
                if not field.validate(value):
                    field_errors.append(f"{field_name} has invalid format")

            # Check string length constraints
            if isinstance(field, StringField) and value is not None:
                if len(str(value)) > field.max_length:
                    field_errors.append(f"{field_name} exceeds maximum length of {field.max_length}")

            if field_errors:
                errors[field_name] = field_errors

        # Run custom validation
        self.clean()

        return errors

    def is_valid(self) -> bool:
        """Check if model instance is valid."""
        return len(self.validate()) == 0

    def clean(self):
        """Override this method to add custom validation logic."""
        pass
    
    @classmethod
    def get_table_name(cls) -> str:
        """Get table name for this model."""
        return cls._table_name
    
    @classmethod
    def get_create_sql(cls) -> str:
        """Generate CREATE TABLE SQL for this model."""
        columns = []
        
        for field_name, field in cls._fields.items():
            column_def = f"{field_name} {field.to_sql_type()}"
            
            if field.primary_key:
                column_def += " PRIMARY KEY"
                if isinstance(field, IntegerField):
                    column_def += " AUTOINCREMENT"
            
            if not field.nullable and not field.primary_key:
                column_def += " NOT NULL"
            
            if field.unique and not field.primary_key:
                column_def += " UNIQUE"
            
            if field.default is not None and not callable(field.default):
                if isinstance(field.default, str):
                    column_def += f" DEFAULT '{field.default}'"
                else:
                    column_def += f" DEFAULT {field.default}"
            
            columns.append(column_def)
        
        return f"CREATE TABLE IF NOT EXISTS {cls.get_table_name()} ({', '.join(columns)})"
    
    def save(self, db: 'Database' = None) -> 'Model':
        """Save model instance to database."""
        if db is None:
            db = Database.get_default()
        
        # Handle auto fields
        for field_name, field in self._fields.items():
            if isinstance(field, DateTimeField):
                if field.auto_now or (field.auto_now_add and self._data.get(field_name) is None):
                    self._data[field_name] = datetime.now()
        
        # Check if this is an insert or update
        pk_field = self._get_pk_field()
        pk_value = self._data.get(pk_field.name) if pk_field else None
        
        if pk_value is None:
            # Insert
            return self._insert(db)
        else:
            # Update
            return self._update(db)
    
    def delete(self, db: 'Database' = None) -> bool:
        """Delete model instance from database."""
        if db is None:
            db = Database.get_default()
        
        pk_field = self._get_pk_field()
        if not pk_field:
            raise ValueError("Cannot delete model without primary key")
        
        pk_value = self._data.get(pk_field.name)
        if pk_value is None:
            return False
        
        sql = f"DELETE FROM {self.get_table_name()} WHERE {pk_field.name} = ?"
        db.execute(sql, (pk_value,))
        return True
    
    def _get_pk_field(self) -> Optional[Field]:
        """Get the primary key field."""
        for field in self._fields.values():
            if field.primary_key:
                return field
        return None
    
    def _insert(self, db: 'Database') -> 'Model':
        """Insert new record."""
        fields = []
        values = []
        placeholders = []
        
        for field_name, field in self._fields.items():
            if field.primary_key and isinstance(field, IntegerField):
                continue  # Skip auto-increment primary keys
            
            value = self._data.get(field_name)
            if value is not None:
                fields.append(field_name)
                values.append(field.to_db(value))
                placeholders.append('?')
        
        if fields:
            sql = f"INSERT INTO {self.get_table_name()} ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
            cursor = db.execute(sql, values)
            
            # Set primary key if auto-increment
            pk_field = self._get_pk_field()
            if pk_field and isinstance(pk_field, IntegerField):
                self._data[pk_field.name] = cursor.lastrowid
        
        self._original_data = self._data.copy()
        return self
    
    def _update(self, db: 'Database') -> 'Model':
        """Update existing record."""
        pk_field = self._get_pk_field()
        pk_value = self._data.get(pk_field.name)
        
        # Find changed fields
        updates = []
        values = []
        
        for field_name, field in self._fields.items():
            if field.primary_key:
                continue
            
            current_value = self._data.get(field_name)
            original_value = self._original_data.get(field_name)
            
            if current_value != original_value:
                updates.append(f"{field_name} = ?")
                values.append(field.to_db(current_value))
        
        if updates:
            sql = f"UPDATE {self.get_table_name()} SET {', '.join(updates)} WHERE {pk_field.name} = ?"
            values.append(pk_value)
            db.execute(sql, values)
        
        self._original_data = self._data.copy()
        return self



class Database:
    """Database connection and query manager with multi-adapter support."""

    _default_instance = None

    def __init__(self, database_path: str = 'wolfpy.db', adapter=None, config: Dict[str, Any] = None):
        """
        Initialize database connection.

        Args:
            database_path: Path to SQLite database file (for backward compatibility)
            adapter: Database adapter instance or adapter class
            config: Database configuration dictionary
        """
        self.database_path = database_path
        self.connection = None
        self.cursor = None
        self.adapter = None

        # Initialize adapter
        if adapter:
            if isinstance(adapter, type):
                # Adapter class provided, instantiate it
                self.adapter = adapter(config or {})
            else:
                # Adapter instance provided
                self.adapter = adapter
        else:
            # Default to SQLite adapter for backward compatibility
            from .adapters.sqlite import SQLiteAdapter
            sqlite_config = config or {"database": database_path}
            self.adapter = SQLiteAdapter(sqlite_config)

        self._connect()
    
    def _connect(self):
        """Connect to database using adapter."""
        if self.adapter:
            self.adapter.connect()
            self.connection = self.adapter.connection
            self.cursor = self.adapter.cursor
        else:
            # Fallback to direct SQLite connection
            self.connection = sqlite3.connect(self.database_path)
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()
    
    @classmethod
    def set_default(cls, database: 'Database'):
        """Set default database instance."""
        cls._default_instance = database
    
    @classmethod
    def get_default(cls) -> 'Database':
        """Get default database instance."""
        if cls._default_instance is None:
            cls._default_instance = cls()
        return cls._default_instance
    
    def execute(self, sql: str, params: tuple = ()) -> Any:
        """Execute SQL query."""
        if self.adapter:
            return self.adapter.execute(sql, params)
        return self.cursor.execute(sql, params)

    def fetchone(self, sql: str, params: tuple = ()) -> Optional[tuple]:
        """Execute query and fetch one result."""
        if self.adapter:
            return self.adapter.fetchone(sql, params)
        self.execute(sql, params)
        return self.cursor.fetchone()

    def fetchall(self, sql: str, params: tuple = ()) -> List[tuple]:
        """Execute query and fetch all results."""
        if self.adapter:
            return self.adapter.fetchall(sql, params)
        self.execute(sql, params)
        return self.cursor.fetchall()

    def commit(self):
        """Commit transaction."""
        if self.adapter:
            self.adapter.commit()
        elif self.connection:
            self.connection.commit()

    def rollback(self):
        """Rollback transaction."""
        if self.adapter:
            self.adapter.rollback()
        elif self.connection:
            self.connection.rollback()

    def close(self):
        """Close database connection."""
        if self.adapter:
            self.adapter.disconnect()
        elif self.connection:
            self.connection.close()

    def table_exists(self, table_name: str) -> bool:
        """Check if table exists."""
        if self.adapter:
            return self.adapter.table_exists(table_name)

        # Fallback for SQLite
        sql = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        result = self.fetchone(sql, (table_name,))
        return result is not None
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        if self.adapter:
            with self.adapter.transaction():
                yield self
        else:
            try:
                yield self
                self.commit()
            except Exception:
                self.rollback()
                raise
    
    def create_tables(self, *model_classes: Type[Model]):
        """Create tables for model classes."""
        for model_class in model_classes:
            sql = model_class.get_create_sql()
            self.execute(sql)
        self.commit()
    
    def objects(self, model_class: Type[Model]) -> QuerySet:
        """Get queryset for model class."""
        return QuerySet(model_class, self)

    def bulk_create(self, model_class: Type[Model], instances: List[Dict[str, Any]]) -> List[Model]:
        """
        Bulk create multiple model instances.

        Args:
            model_class: Model class
            instances: List of dictionaries with field values

        Returns:
            List of created model instances
        """
        if not instances:
            return []

        # Prepare bulk insert
        fields = list(instances[0].keys())
        placeholders = ', '.join(['?' for _ in fields])
        sql = f"INSERT INTO {model_class.get_table_name()} ({', '.join(fields)}) VALUES ({placeholders})"

        # Prepare values
        values_list = []
        for instance_data in instances:
            values = []
            for field_name in fields:
                value = instance_data.get(field_name)
                field = model_class._fields.get(field_name)
                if field:
                    value = field.to_db(value)
                values.append(value)
            values_list.append(values)

        # Execute bulk insert
        with self.transaction():
            self.cursor.executemany(sql, values_list)

        # Return model instances
        created_instances = []
        for instance_data in instances:
            instance = model_class(**instance_data)
            instance._original_data = instance._data.copy()
            created_instances.append(instance)

        return created_instances

    def bulk_update(self, model_class: Type[Model], instances: List[Model]) -> int:
        """
        Bulk update multiple model instances.

        Args:
            model_class: Model class
            instances: List of model instances to update

        Returns:
            Number of updated records
        """
        if not instances:
            return 0

        pk_field = None
        for field in model_class._fields.values():
            if field.primary_key:
                pk_field = field
                break

        if not pk_field:
            raise ValueError("Cannot bulk update models without primary key")

        updated_count = 0
        with self.transaction():
            for instance in instances:
                # Find changed fields
                updates = []
                values = []

                for field_name, field in model_class._fields.items():
                    if field.primary_key:
                        continue

                    current_value = instance._data.get(field_name)
                    original_value = instance._original_data.get(field_name)

                    if current_value != original_value:
                        updates.append(f"{field_name} = ?")
                        values.append(field.to_db(current_value))

                if updates:
                    pk_value = instance._data.get(pk_field.name)
                    sql = f"UPDATE {model_class.get_table_name()} SET {', '.join(updates)} WHERE {pk_field.name} = ?"
                    values.append(pk_value)
                    self.execute(sql, values)
                    updated_count += 1

                    # Update original data
                    instance._original_data = instance._data.copy()

        return updated_count


class QueryOptimizer:
    """
    Query optimizer for improving database performance.
    """

    def __init__(self):
        self.optimization_rules = {
            'index_suggestions': self._suggest_indexes,
            'query_rewriting': self._rewrite_query,
            'join_optimization': self._optimize_joins
        }
        self.query_patterns = {}
        self.performance_stats = {}

    def optimize_query(self, sql: str, params: tuple = ()) -> Tuple[str, tuple]:
        """
        Optimize SQL query for better performance.

        Args:
            sql: Original SQL query
            params: Query parameters

        Returns:
            Tuple of (optimized_sql, optimized_params)
        """
        optimized_sql = sql
        optimized_params = params

        # Apply optimization rules
        for rule_name, rule_func in self.optimization_rules.items():
            try:
                optimized_sql, optimized_params = rule_func(optimized_sql, optimized_params)
            except Exception as e:
                print(f"Optimization rule {rule_name} failed: {e}")

        return optimized_sql, optimized_params

    def _suggest_indexes(self, sql: str, params: tuple) -> Tuple[str, tuple]:
        """Suggest indexes for query optimization."""
        # Analyze WHERE clauses and suggest indexes
        # This is a simplified implementation
        return sql, params

    def _rewrite_query(self, sql: str, params: tuple) -> Tuple[str, tuple]:
        """Rewrite query for better performance."""
        # Simple query rewriting rules
        if 'SELECT *' in sql.upper():
            # Suggest specific column selection
            pass

        return sql, params

    def _optimize_joins(self, sql: str, params: tuple) -> Tuple[str, tuple]:
        """Optimize JOIN operations."""
        # Analyze and optimize JOIN order
        return sql, params

    def analyze_query_performance(self, sql: str, execution_time: float):
        """Analyze query performance and store statistics."""
        query_hash = hash(sql)

        if query_hash not in self.performance_stats:
            self.performance_stats[query_hash] = {
                'sql': sql,
                'execution_count': 0,
                'total_time': 0.0,
                'avg_time': 0.0,
                'max_time': 0.0,
                'min_time': float('inf')
            }

        stats = self.performance_stats[query_hash]
        stats['execution_count'] += 1
        stats['total_time'] += execution_time
        stats['avg_time'] = stats['total_time'] / stats['execution_count']
        stats['max_time'] = max(stats['max_time'], execution_time)
        stats['min_time'] = min(stats['min_time'], execution_time)

    def get_slow_queries(self, threshold: float = 1.0) -> List[Dict[str, Any]]:
        """Get queries that exceed performance threshold."""
        slow_queries = []

        for stats in self.performance_stats.values():
            if stats['avg_time'] > threshold:
                slow_queries.append(stats)

        return sorted(slow_queries, key=lambda x: x['avg_time'], reverse=True)


class DatabasePerformanceMonitor:
    """
    Monitor database performance and provide insights.
    """

    def __init__(self):
        self.query_log = []
        self.connection_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'failed_connections': 0,
            'avg_connection_time': 0.0
        }
        self.transaction_stats = {
            'total_transactions': 0,
            'committed_transactions': 0,
            'rolled_back_transactions': 0,
            'avg_transaction_time': 0.0
        }

    def log_query(self, sql: str, params: tuple, execution_time: float, success: bool):
        """Log query execution for monitoring."""
        log_entry = {
            'timestamp': time.time(),
            'sql': sql,
            'params': params,
            'execution_time': execution_time,
            'success': success
        }

        self.query_log.append(log_entry)

        # Keep only recent entries (last 1000)
        if len(self.query_log) > 1000:
            self.query_log = self.query_log[-1000:]

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report."""
        if not self.query_log:
            return {'message': 'No query data available'}

        total_queries = len(self.query_log)
        successful_queries = sum(1 for entry in self.query_log if entry['success'])
        failed_queries = total_queries - successful_queries

        execution_times = [entry['execution_time'] for entry in self.query_log]
        avg_execution_time = sum(execution_times) / len(execution_times)
        max_execution_time = max(execution_times)
        min_execution_time = min(execution_times)

        return {
            'total_queries': total_queries,
            'successful_queries': successful_queries,
            'failed_queries': failed_queries,
            'success_rate': (successful_queries / total_queries) * 100,
            'avg_execution_time': avg_execution_time,
            'max_execution_time': max_execution_time,
            'min_execution_time': min_execution_time,
            'connection_stats': self.connection_stats,
            'transaction_stats': self.transaction_stats
        }


class ConnectionPool:
    """
    Advanced database connection pool with health monitoring.
    """

    def __init__(self, database_url: str, min_connections: int = 2,
                 max_connections: int = 10, connection_timeout: int = 30):
        self.database_url = database_url
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout

        self._pool = []
        self._active_connections = set()
        self._connection_stats = {
            'created': 0,
            'destroyed': 0,
            'borrowed': 0,
            'returned': 0,
            'timeouts': 0
        }
        self._lock = threading.Lock()

        # Initialize minimum connections
        self._initialize_pool()

    def _initialize_pool(self):
        """Initialize the connection pool with minimum connections."""
        for _ in range(self.min_connections):
            conn = self._create_connection()
            if conn:
                self._pool.append(conn)

    def _create_connection(self):
        """Create a new database connection."""
        try:
            import sqlite3
            conn = sqlite3.connect(self.database_url, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            self._connection_stats['created'] += 1
            return conn
        except Exception as e:
            print(f"Failed to create connection: {e}")
            return None

    def get_connection(self, timeout: int = None):
        """Get a connection from the pool."""
        timeout = timeout or self.connection_timeout
        start_time = time.time()

        while time.time() - start_time < timeout:
            with self._lock:
                # Try to get connection from pool
                if self._pool:
                    conn = self._pool.pop()
                    self._active_connections.add(conn)
                    self._connection_stats['borrowed'] += 1
                    return conn

                # Create new connection if under limit
                if len(self._active_connections) < self.max_connections:
                    conn = self._create_connection()
                    if conn:
                        self._active_connections.add(conn)
                        self._connection_stats['borrowed'] += 1
                        return conn

            # Wait a bit before retrying
            time.sleep(0.1)

        self._connection_stats['timeouts'] += 1
        raise TimeoutError("Connection pool timeout")

    def return_connection(self, conn):
        """Return a connection to the pool."""
        with self._lock:
            if conn in self._active_connections:
                self._active_connections.remove(conn)

                # Check if connection is still healthy
                if self._is_connection_healthy(conn):
                    self._pool.append(conn)
                    self._connection_stats['returned'] += 1
                else:
                    conn.close()
                    self._connection_stats['destroyed'] += 1

    def _is_connection_healthy(self, conn) -> bool:
        """Check if connection is still healthy."""
        try:
            conn.execute("SELECT 1")
            return True
        except:
            return False

    def close_all(self):
        """Close all connections in the pool."""
        with self._lock:
            # Close pooled connections
            for conn in self._pool:
                conn.close()
            self._pool.clear()

            # Close active connections
            for conn in self._active_connections:
                conn.close()
            self._active_connections.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        with self._lock:
            return {
                'pool_size': len(self._pool),
                'active_connections': len(self._active_connections),
                'max_connections': self.max_connections,
                'stats': self._connection_stats.copy()
            }


class ManyToManyField:
    """
    Many-to-many relationship field.
    """

    def __init__(self, related_model: str, through: str = None,
                 related_name: str = None):
        self.related_model = related_model
        self.through = through  # Intermediate table name
        self.related_name = related_name
        self.field_name = None  # Set by metaclass

    def contribute_to_class(self, model_class, field_name):
        """Called when field is added to model."""
        self.field_name = field_name
        self.model_class = model_class

        # Create through table name if not specified
        if not self.through:
            model_names = sorted([model_class.__name__.lower(), self.related_model.lower()])
            self.through = f"{model_names[0]}_{model_names[1]}"

    def get_related_objects(self, instance):
        """Get related objects for this instance."""
        # This would be implemented with proper SQL joins
        # For now, return empty list
        return []

    def add(self, instance, *objects):
        """Add objects to the many-to-many relationship."""
        # Implementation would insert into through table
        pass

    def remove(self, instance, *objects):
        """Remove objects from the many-to-many relationship."""
        # Implementation would delete from through table
        pass


class LazyLoader:
    """
    Lazy loading mechanism for related objects.
    """

    def __init__(self, field, instance):
        self.field = field
        self.instance = instance
        self._loaded = False
        self._value = None

    def __get__(self, instance, owner):
        if not self._loaded:
            self._load()
        return self._value

    def _load(self):
        """Load the related object(s)."""
        # Implementation would query the database
        self._loaded = True
        self._value = None  # Placeholder


class DatabaseIntrospector:
    """
    Database introspection for automatic model generation.
    """

    def __init__(self, database):
        self.database = database

    def get_table_names(self) -> List[str]:
        """Get all table names in the database."""
        cursor = self.database.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return [row[0] for row in cursor.fetchall()]

    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get schema information for a table."""
        cursor = self.database.connection.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")

        columns = []
        for row in cursor.fetchall():
            columns.append({
                'name': row[1],
                'type': row[2],
                'nullable': not row[3],
                'default': row[4],
                'primary_key': bool(row[5])
            })

        return {
            'table_name': table_name,
            'columns': columns
        }

    def generate_model_code(self, table_name: str) -> str:
        """Generate Python model code for a table."""
        schema = self.get_table_schema(table_name)

        # Map SQLite types to field types
        type_mapping = {
            'INTEGER': 'IntegerField',
            'TEXT': 'StringField',
            'REAL': 'FloatField',
            'BLOB': 'BlobField'
        }

        class_name = ''.join(word.capitalize() for word in table_name.split('_'))

        code = f"class {class_name}(Model):\n"
        code += f'    __tablename__ = "{table_name}"\n\n'

        for column in schema['columns']:
            field_type = type_mapping.get(column['type'], 'StringField')
            field_args = []

            if column['primary_key']:
                field_args.append('primary_key=True')
            if not column['nullable']:
                field_args.append('nullable=False')

            args_str = ', '.join(field_args)
            if args_str:
                args_str = f'({args_str})'

            code += f"    {column['name']} = {field_type}{args_str}\n"

        return code


class DatabaseShardManager:
    """
    Database sharding manager for horizontal scaling.
    """

    def __init__(self, shard_configs: List[Dict[str, Any]]):
        self.shards = {}
        self.shard_ring = []
        self.total_shards = len(shard_configs)

        # Initialize shards
        for i, config in enumerate(shard_configs):
            shard_id = f"shard_{i}"
            self.shards[shard_id] = Database(
                database_path=config['url'],
                config=config.get('config', {})
            )
            self.shard_ring.append(shard_id)

    def get_shard_for_key(self, key: str) -> Database:
        """Get appropriate shard for a given key."""
        # Simple hash-based sharding
        shard_index = hash(key) % self.total_shards
        shard_id = self.shard_ring[shard_index]
        return self.shards[shard_id]

    def get_shard_by_id(self, shard_id: str) -> Optional[Database]:
        """Get shard by ID."""
        return self.shards.get(shard_id)

    def execute_on_all_shards(self, sql: str, params: tuple = ()) -> List[Any]:
        """Execute query on all shards."""
        results = []
        for shard_id, shard in self.shards.items():
            try:
                result = shard.execute(sql, params)
                results.append({'shard_id': shard_id, 'result': result})
            except Exception as e:
                results.append({'shard_id': shard_id, 'error': str(e)})
        return results

    def get_shard_statistics(self) -> Dict[str, Any]:
        """Get statistics for all shards."""
        stats = {}
        for shard_id, shard in self.shards.items():
            try:
                # Get basic stats (would be more comprehensive in real implementation)
                stats[shard_id] = {
                    'status': 'healthy',
                    'connection_count': getattr(shard, '_connection_count', 0),
                    'last_query_time': getattr(shard, '_last_query_time', 0)
                }
            except Exception as e:
                stats[shard_id] = {
                    'status': 'error',
                    'error': str(e)
                }
        return stats


class ReadWriteSplitter:
    """
    Read/Write splitting for database performance optimization.
    """

    def __init__(self, master_db: Database, read_replicas: List[Database]):
        self.master_db = master_db
        self.read_replicas = read_replicas
        self.current_replica_index = 0
        self.replica_health = {i: True for i in range(len(read_replicas))}

    def execute_read(self, sql: str, params: tuple = ()) -> Any:
        """Execute read query on replica."""
        # Try to use a healthy replica
        for _ in range(len(self.read_replicas)):
            replica_index = self._get_next_replica()
            if self.replica_health[replica_index]:
                try:
                    return self.read_replicas[replica_index].execute(sql, params)
                except Exception as e:
                    # Mark replica as unhealthy
                    self.replica_health[replica_index] = False
                    print(f"Replica {replica_index} failed: {e}")
                    continue

        # Fallback to master if all replicas are down
        print("All replicas down, falling back to master for read")
        return self.master_db.execute(sql, params)

    def execute_write(self, sql: str, params: tuple = ()) -> Any:
        """Execute write query on master."""
        return self.master_db.execute(sql, params)

    def _get_next_replica(self) -> int:
        """Get next replica using round-robin."""
        replica_index = self.current_replica_index
        self.current_replica_index = (self.current_replica_index + 1) % len(self.read_replicas)
        return replica_index

    def check_replica_health(self):
        """Check health of all replicas."""
        for i, replica in enumerate(self.read_replicas):
            try:
                replica.execute("SELECT 1")
                self.replica_health[i] = True
            except Exception:
                self.replica_health[i] = False

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all databases."""
        return {
            'master': self._check_db_health(self.master_db),
            'replicas': [
                {
                    'index': i,
                    'healthy': self.replica_health[i],
                    'status': self._check_db_health(replica)
                }
                for i, replica in enumerate(self.read_replicas)
            ]
        }

    def _check_db_health(self, db: Database) -> Dict[str, Any]:
        """Check health of a single database."""
        try:
            start_time = time.time()
            db.execute("SELECT 1")
            response_time = time.time() - start_time
            return {
                'status': 'healthy',
                'response_time': response_time
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }


class DatabaseMigrationManager:
    """
    Advanced database migration manager with rollback support.
    """

    def __init__(self, database: Database, migrations_dir: str = 'migrations'):
        self.database = database
        self.migrations_dir = migrations_dir
        self.migration_table = 'schema_migrations'
        self._ensure_migration_table()

    def _ensure_migration_table(self):
        """Ensure migration tracking table exists."""
        sql = f"""
        CREATE TABLE IF NOT EXISTS {self.migration_table} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            rollback_sql TEXT
        )
        """
        self.database.execute(sql)

    def create_migration(self, name: str) -> str:
        """Create a new migration file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        version = f"{timestamp}_{name}"

        migration_content = f"""
# Migration: {name}
# Version: {version}
# Created: {datetime.now().isoformat()}

def up(db):
    \"\"\"Apply migration.\"\"\"
    # Add your migration SQL here
    db.execute(\"\"\"
        -- Your SQL here
    \"\"\")

def down(db):
    \"\"\"Rollback migration.\"\"\"
    # Add your rollback SQL here
    db.execute(\"\"\"
        -- Your rollback SQL here
    \"\"\")
"""

        # Create migrations directory if it doesn't exist
        os.makedirs(self.migrations_dir, exist_ok=True)

        # Write migration file
        migration_file = os.path.join(self.migrations_dir, f"{version}.py")
        with open(migration_file, 'w') as f:
            f.write(migration_content)

        return migration_file

    def get_pending_migrations(self) -> List[str]:
        """Get list of pending migrations."""
        # Get applied migrations
        applied = set()
        try:
            result = self.database.execute(f"SELECT version FROM {self.migration_table}")
            applied = {row[0] for row in result}
        except:
            pass

        # Get all migration files
        all_migrations = []
        if os.path.exists(self.migrations_dir):
            for filename in os.listdir(self.migrations_dir):
                if filename.endswith('.py') and not filename.startswith('__'):
                    version = filename[:-3]  # Remove .py extension
                    all_migrations.append(version)

        # Return pending migrations
        all_migrations.sort()
        return [m for m in all_migrations if m not in applied]

    def apply_migration(self, version: str) -> bool:
        """Apply a specific migration."""
        migration_file = os.path.join(self.migrations_dir, f"{version}.py")

        if not os.path.exists(migration_file):
            raise ValueError(f"Migration file not found: {migration_file}")

        try:
            # Load migration module
            import importlib.util
            spec = importlib.util.spec_from_file_location(version, migration_file)
            migration_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(migration_module)

            # Start transaction
            with self.database.transaction():
                # Apply migration
                migration_module.up(self.database)

                # Record migration
                self.database.execute(
                    f"INSERT INTO {self.migration_table} (version, name) VALUES (?, ?)",
                    (version, version.split('_', 1)[1] if '_' in version else version)
                )

            print(f"Applied migration: {version}")
            return True

        except Exception as e:
            print(f"Failed to apply migration {version}: {e}")
            return False

    def rollback_migration(self, version: str) -> bool:
        """Rollback a specific migration."""
        migration_file = os.path.join(self.migrations_dir, f"{version}.py")

        if not os.path.exists(migration_file):
            raise ValueError(f"Migration file not found: {migration_file}")

        try:
            # Load migration module
            import importlib.util
            spec = importlib.util.spec_from_file_location(version, migration_file)
            migration_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(migration_module)

            # Start transaction
            with self.database.transaction():
                # Rollback migration
                migration_module.down(self.database)

                # Remove migration record
                self.database.execute(
                    f"DELETE FROM {self.migration_table} WHERE version = ?",
                    (version,)
                )

            print(f"Rolled back migration: {version}")
            return True

        except Exception as e:
            print(f"Failed to rollback migration {version}: {e}")
            return False

    def migrate_up(self) -> int:
        """Apply all pending migrations."""
        pending = self.get_pending_migrations()
        applied_count = 0

        for version in pending:
            if self.apply_migration(version):
                applied_count += 1
            else:
                break  # Stop on first failure

        return applied_count

    def get_migration_status(self) -> Dict[str, Any]:
        """Get migration status."""
        applied = []
        try:
            result = self.database.execute(
                f"SELECT version, name, applied_at FROM {self.migration_table} ORDER BY applied_at"
            )
            applied = [{'version': row[0], 'name': row[1], 'applied_at': row[2]} for row in result]
        except:
            pass

        pending = self.get_pending_migrations()

        return {
            'applied_migrations': applied,
            'pending_migrations': pending,
            'total_applied': len(applied),
            'total_pending': len(pending)
        }
