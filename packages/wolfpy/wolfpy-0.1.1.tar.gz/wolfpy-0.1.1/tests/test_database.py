"""
Tests for WolfPy Database ORM System.

This test suite covers the enhanced database functionality including:
- Model definition and field types
- QuerySet operations and filtering
- Relationships (Foreign Key, Many-to-Many)
- Model validation
- Database operations (CRUD)
"""

import os
import tempfile
import pytest
from datetime import datetime

from src.wolfpy.core.database import (
    Database, Model, QuerySet, ModelManager,
    IntegerField, StringField, TextField, BooleanField,
    DateTimeField, EmailField, URLField, DecimalField,
    ForeignKeyField, ManyToManyField, OneToOneField,
    QueryOperator, QueryFilter
)


class TestFieldTypes:
    """Test various field types and their validation."""
    
    def test_integer_field(self):
        """Test IntegerField functionality."""
        field = IntegerField(primary_key=True)
        
        assert field.to_sql_type() == "INTEGER"
        assert field.to_python("123") == 123
        assert field.to_python(None) is None
    
    def test_string_field(self):
        """Test StringField functionality."""
        field = StringField(max_length=50)
        
        assert field.to_sql_type() == "VARCHAR(50)"
        assert field.to_python("test") == "test"
        assert field.to_python(123) == "123"
    
    def test_email_field(self):
        """Test EmailField validation."""
        field = EmailField()
        
        # Valid emails
        assert field.validate("test@example.com")
        assert field.validate("user.name+tag@domain.co.uk")
        
        # Invalid emails
        assert not field.validate("invalid-email")
        assert not field.validate("@domain.com")
        assert not field.validate("user@")
    
    def test_url_field(self):
        """Test URLField validation."""
        field = URLField()
        
        # Valid URLs
        assert field.validate("https://example.com")
        assert field.validate("http://subdomain.example.com:8080/path")
        
        # Invalid URLs
        assert not field.validate("not-a-url")
        assert not field.validate("ftp://example.com")  # Only http/https supported
    
    def test_datetime_field(self):
        """Test DateTimeField functionality."""
        field = DateTimeField(auto_now_add=True)
        
        now = datetime.now()
        iso_string = now.isoformat()
        
        assert field.to_python(iso_string) == now
        assert field.to_db(now) == iso_string


class TestModelDefinition:
    """Test model definition and basic operations."""
    
    def setup_method(self):
        """Set up test database and models."""
        self.db_file = tempfile.mktemp(suffix='.db')
        self.db = Database(self.db_file)
        
        # Define test models
        class User(Model):
            id = IntegerField(primary_key=True)
            username = StringField(max_length=50, unique=True)
            email = EmailField()
            is_active = BooleanField(default=True)
            created_at = DateTimeField(auto_now_add=True)
        
        class Post(Model):
            id = IntegerField(primary_key=True)
            title = StringField(max_length=200)
            content = TextField()
            author = ForeignKeyField(User)
            published = BooleanField(default=False)
            created_at = DateTimeField(auto_now_add=True)
        
        self.User = User
        self.Post = Post
        
        # Create tables
        self.db.create_tables(User, Post)
    
    def teardown_method(self):
        """Clean up test database."""
        # Close database connection first
        if hasattr(self, 'db') and self.db:
            self.db.close()

        # Then remove file
        if os.path.exists(self.db_file):
            try:
                os.unlink(self.db_file)
            except PermissionError:
                # On Windows, sometimes the file is still locked
                import time
                time.sleep(0.1)
                try:
                    os.unlink(self.db_file)
                except PermissionError:
                    pass  # Ignore if still can't delete
    
    def test_model_creation(self):
        """Test creating and saving model instances."""
        user = self.User(
            username="testuser",
            email="test@example.com",
            is_active=True
        )
        
        # Test field access
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active is True
        
        # Save to database
        user.save(self.db)
        assert user.id is not None
        
        # Test retrieval
        retrieved_user = self.User.objects.get(self.db, id=user.id)
        assert retrieved_user.username == "testuser"
        assert retrieved_user.email == "test@example.com"
    
    def test_model_validation(self):
        """Test model validation."""
        # Valid user
        valid_user = self.User(
            username="validuser",
            email="valid@example.com"
        )
        assert valid_user.is_valid()
        
        # Invalid email
        invalid_user = self.User(
            username="invaliduser",
            email="invalid-email"
        )
        assert not invalid_user.is_valid()
        
        errors = invalid_user.validate()
        assert "email" in errors
    
    def test_foreign_key_relationship(self):
        """Test foreign key relationships."""
        # Create user
        user = self.User(username="author", email="author@example.com")
        user.save(self.db)
        
        # Create post with foreign key
        post = self.Post(
            title="Test Post",
            content="This is a test post",
            author=user.id,
            published=True
        )
        post.save(self.db)
        
        assert post.id is not None
        assert post.author == user.id
        
        # Retrieve and verify
        retrieved_post = self.Post.objects.get(self.db, id=post.id)
        assert retrieved_post.author == user.id


class TestQuerySet:
    """Test QuerySet operations and filtering."""
    
    def setup_method(self):
        """Set up test database with sample data."""
        self.db_file = tempfile.mktemp(suffix='.db')
        self.db = Database(self.db_file)
        
        class User(Model):
            id = IntegerField(primary_key=True)
            username = StringField(max_length=50)
            email = EmailField()
            age = IntegerField()
            is_active = BooleanField(default=True)
        
        self.User = User
        self.db.create_tables(User)
        
        # Create sample data
        users_data = [
            {"username": "alice", "email": "alice@example.com", "age": 25, "is_active": True},
            {"username": "bob", "email": "bob@example.com", "age": 30, "is_active": True},
            {"username": "charlie", "email": "charlie@example.com", "age": 35, "is_active": False},
            {"username": "diana", "email": "diana@example.com", "age": 28, "is_active": True},
        ]
        
        for data in users_data:
            user = User(**data)
            user.save(self.db)
    
    def teardown_method(self):
        """Clean up test database."""
        # Close database connection first
        if hasattr(self, 'db') and self.db:
            self.db.close()

        # Then remove file
        if os.path.exists(self.db_file):
            try:
                os.unlink(self.db_file)
            except PermissionError:
                # On Windows, sometimes the file is still locked
                import time
                time.sleep(0.1)
                try:
                    os.unlink(self.db_file)
                except PermissionError:
                    pass  # Ignore if still can't delete
    
    def test_basic_queries(self):
        """Test basic QuerySet operations."""
        # Get all users (returns QuerySet)
        all_users_qs = self.User.objects.all(self.db)
        all_users = all_users_qs.all()  # Convert to list
        assert len(all_users) == 4

        # Count users
        count = self.User.objects.count(self.db)
        assert count == 4

        # Check existence
        exists = self.User.objects.exists(self.db)
        assert exists is True
    
    def test_filtering(self):
        """Test QuerySet filtering."""
        # Filter by exact match
        active_users_qs = self.User.objects.filter(self.db, is_active=True)
        active_users = active_users_qs.all()
        assert len(active_users) == 3

        # Filter by age
        young_users_qs = self.User.objects.filter(self.db, age=25)
        young_users = young_users_qs.all()
        assert len(young_users) == 1
        assert young_users[0].username == "alice"

        # Multiple filters
        young_active_qs = self.User.objects.filter(
            self.db,
            age=25,
            is_active=True
        )
        young_active = young_active_qs.all()
        assert len(young_active) == 1
    
    def test_advanced_filtering(self):
        """Test advanced QuerySet filtering with lookups."""
        qs = QuerySet(self.User, self.db)
        
        # Test greater than
        older_users = qs.filter(age__gt=28)
        results = older_users.all()
        assert len(results) >= 2  # bob and charlie
        
        # Test less than or equal
        younger_users = qs.filter(age__lte=28)
        results = younger_users.all()
        assert len(results) >= 2  # alice and diana
        
        # Test contains (would work with string fields)
        users_with_a = qs.filter(username__contains="a")
        results = users_with_a.all()
        assert len(results) >= 2  # alice and diana
    
    def test_ordering(self):
        """Test QuerySet ordering."""
        # Order by age ascending
        users_by_age = self.User.objects.all(self.db).order_by("age")
        results = users_by_age.all()
        ages = [user.age for user in results]
        assert ages == sorted(ages)
        
        # Order by age descending
        users_by_age_desc = self.User.objects.all(self.db).order_by("-age")
        results = users_by_age_desc.all()
        ages = [user.age for user in results]
        assert ages == sorted(ages, reverse=True)
    
    def test_limit_and_offset(self):
        """Test QuerySet limit and offset."""
        # Limit results
        limited_users = self.User.objects.all(self.db).limit(2)
        results = limited_users.all()
        assert len(results) == 2
        
        # Offset results
        offset_users = self.User.objects.all(self.db).offset(1).limit(2)
        results = offset_users.all()
        assert len(results) == 2
        
        # Test pagination
        page1 = self.User.objects.all(self.db).limit(2)
        page2 = self.User.objects.all(self.db).offset(2).limit(2)
        
        page1_results = page1.all()
        page2_results = page2.all()
        
        assert len(page1_results) == 2
        assert len(page2_results) == 2
        
        # Ensure no overlap
        page1_ids = {user.id for user in page1_results}
        page2_ids = {user.id for user in page2_results}
        assert page1_ids.isdisjoint(page2_ids)
    
    def test_get_single_object(self):
        """Test getting single objects."""
        # Get existing user
        alice = self.User.objects.get(self.db, username="alice")
        assert alice.username == "alice"
        assert alice.email == "alice@example.com"
        
        # Test get with non-existent user
        with pytest.raises(ValueError):
            self.User.objects.get(self.db, username="nonexistent")
    
    def test_first_and_last(self):
        """Test first() and last() methods."""
        qs = self.User.objects.all(self.db).order_by("age")
        
        # Get first (youngest)
        first_user = qs.first()
        assert first_user is not None
        assert first_user.age == 25  # alice
        
        # Get last (oldest)
        last_user = qs.last()
        assert last_user is not None
        assert last_user.age == 35  # charlie
    
    def test_exclude(self):
        """Test QuerySet exclude functionality."""
        # Exclude inactive users
        active_users = self.User.objects.exclude(self.db, is_active=False)
        results = active_users.all()
        assert len(results) == 3
        
        for user in results:
            assert user.is_active is True
    
    def test_chaining_operations(self):
        """Test chaining QuerySet operations."""
        # Chain multiple operations
        result = (self.User.objects
                 .filter(self.db, is_active=True)
                 .exclude(age=35)
                 .order_by("-age")
                 .limit(2))
        
        users = result.all()
        assert len(users) <= 2
        
        for user in users:
            assert user.is_active is True
            assert user.age != 35


class TestModelManager:
    """Test ModelManager functionality."""
    
    def setup_method(self):
        """Set up test database."""
        self.db_file = tempfile.mktemp(suffix='.db')
        self.db = Database(self.db_file)
        
        class User(Model):
            id = IntegerField(primary_key=True)
            username = StringField(max_length=50)
            email = EmailField()
        
        self.User = User
        self.db.create_tables(User)
    
    def teardown_method(self):
        """Clean up test database."""
        # Close database connection first
        if hasattr(self, 'db') and self.db:
            self.db.close()

        # Then remove file
        if os.path.exists(self.db_file):
            try:
                os.unlink(self.db_file)
            except PermissionError:
                # On Windows, sometimes the file is still locked
                import time
                time.sleep(0.1)
                try:
                    os.unlink(self.db_file)
                except PermissionError:
                    pass  # Ignore if still can't delete
    
    def test_create_method(self):
        """Test ModelManager.create() method."""
        user = self.User.objects.create(
            db=self.db,
            username="created_user",
            email="created@example.com"
        )
        
        assert user.id is not None
        assert user.username == "created_user"
        
        # Verify it's saved in database
        retrieved = self.User.objects.get(self.db, id=user.id)
        assert retrieved.username == "created_user"
    
    def test_bulk_create(self):
        """Test bulk creation of objects."""
        users = [
            self.User(username=f"user{i}", email=f"user{i}@example.com")
            for i in range(5)
        ]
        
        created_users = self.User.objects.bulk_create(users, self.db)
        assert len(created_users) == 5
        
        # Verify all are saved
        count = self.User.objects.count(self.db)
        assert count == 5


class TestQueryFilters:
    """Test QueryFilter functionality."""
    
    def test_query_filter_creation(self):
        """Test creating QueryFilter objects."""
        # Equals filter
        filter_eq = QueryFilter("name", QueryOperator.EQUALS, "test")
        sql, params = filter_eq.to_sql()
        assert sql == "name = ?"
        assert params == ["test"]
        
        # IN filter
        filter_in = QueryFilter("id", QueryOperator.IN, [1, 2, 3])
        sql, params = filter_in.to_sql()
        assert sql == "id IN (?,?,?)"
        assert params == [1, 2, 3]
        
        # IS NULL filter
        filter_null = QueryFilter("deleted_at", QueryOperator.IS_NULL)
        sql, params = filter_null.to_sql()
        assert sql == "deleted_at IS NULL"
        assert params == []
        
        # BETWEEN filter
        filter_between = QueryFilter("age", QueryOperator.BETWEEN, [18, 65])
        sql, params = filter_between.to_sql()
        assert sql == "age BETWEEN ? AND ?"
        assert params == [18, 65]


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
