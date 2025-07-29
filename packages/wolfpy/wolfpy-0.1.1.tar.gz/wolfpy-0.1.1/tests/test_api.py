"""
Tests for WolfPy Advanced API System.

This test suite covers the enhanced API functionality including:
- API Framework setup and configuration
- Rate limiting and throttling
- Pagination and serialization
- API versioning
- Error handling and responses
- Request/response validation
"""

import pytest
import json
import time
from unittest.mock import MagicMock, patch

from src.wolfpy import WolfPy
from src.wolfpy.core.api import (
    APIFramework, APIModel, APIField, APISerializer,
    PaginationInfo, RateLimiter, APIVersionManager,
    paginate_data, create_error_response,
    APIError, ValidationError, RateLimitError
)
from src.wolfpy.core.request import Request
from src.wolfpy.core.response import Response


class TestPagination:
    """Test pagination functionality."""
    
    def test_pagination_info_creation(self):
        """Test creating PaginationInfo from request."""
        # Mock request with pagination parameters
        mock_request = MagicMock()
        mock_request.args = {'page': '2', 'per_page': '5'}
        
        pagination = PaginationInfo.from_request(mock_request)
        
        assert pagination.page == 2
        assert pagination.per_page == 5
        assert pagination.get_offset() == 5  # (page-1) * per_page
    
    def test_pagination_calculation(self):
        """Test pagination calculations."""
        pagination = PaginationInfo(page=3, per_page=10)
        pagination.calculate_pagination(total_items=45)
        
        assert pagination.total_items == 45
        assert pagination.total_pages == 5  # ceil(45/10)
        assert pagination.has_prev is True
        assert pagination.has_next is True
        assert pagination.prev_page == 2
        assert pagination.next_page == 4
    
    def test_pagination_edge_cases(self):
        """Test pagination edge cases."""
        # First page
        pagination = PaginationInfo(page=1, per_page=10)
        pagination.calculate_pagination(total_items=25)
        
        assert pagination.has_prev is False
        assert pagination.prev_page is None
        assert pagination.has_next is True
        
        # Last page
        pagination = PaginationInfo(page=3, per_page=10)
        pagination.calculate_pagination(total_items=25)
        
        assert pagination.has_prev is True
        assert pagination.has_next is False
        assert pagination.next_page is None
    
    def test_paginate_data_function(self):
        """Test paginate_data helper function."""
        data = list(range(1, 26))  # 25 items
        pagination = PaginationInfo(page=2, per_page=10)
        
        result = paginate_data(data, pagination)
        
        assert len(result['data']) == 10
        assert result['data'][0] == 11  # Second page starts at item 11
        assert result['pagination']['total_items'] == 25
        assert result['pagination']['total_pages'] == 3
        assert result['pagination']['has_next'] is True
        assert result['pagination']['has_prev'] is True


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limiter_basic(self):
        """Test basic rate limiting."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        client_id = "test_client"
        
        # First 3 requests should be allowed
        for i in range(3):
            allowed, retry_after = limiter.is_allowed(client_id)
            assert allowed is True
            assert retry_after is None
        
        # 4th request should be denied
        allowed, retry_after = limiter.is_allowed(client_id)
        assert allowed is False
        assert retry_after is not None
        assert retry_after > 0
    
    def test_rate_limiter_remaining(self):
        """Test getting remaining requests."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        client_id = "test_client"
        
        # Initially should have 5 remaining
        remaining = limiter.get_remaining(client_id)
        assert remaining == 5
        
        # After 2 requests, should have 3 remaining
        limiter.is_allowed(client_id)
        limiter.is_allowed(client_id)
        
        remaining = limiter.get_remaining(client_id)
        assert remaining == 3
    
    def test_rate_limiter_window_reset(self):
        """Test rate limiter window reset."""
        limiter = RateLimiter(max_requests=2, window_seconds=1)
        client_id = "test_client"
        
        # Use up the limit
        limiter.is_allowed(client_id)
        limiter.is_allowed(client_id)
        
        # Should be denied
        allowed, _ = limiter.is_allowed(client_id)
        assert allowed is False
        
        # Wait for window to reset
        time.sleep(1.1)
        
        # Should be allowed again
        allowed, _ = limiter.is_allowed(client_id)
        assert allowed is True


class TestAPISerialization:
    """Test API serialization functionality."""
    
    def test_basic_serialization(self):
        """Test basic object serialization."""
        serializer = APISerializer()
        
        data = {
            'id': 1,
            'name': 'Test Item',
            'active': True,
            '_private': 'should be excluded',
            'nested': {
                'id': 2,
                'value': 'nested value'
            }
        }
        
        result = serializer.serialize(data)
        
        assert result['id'] == 1
        assert result['name'] == 'Test Item'
        assert result['active'] is True
        assert '_private' not in result  # Private fields excluded
        assert 'nested' in result
        assert result['nested']['id'] == 2
    
    def test_field_filtering(self):
        """Test serialization with field filtering."""
        data = {
            'id': 1,
            'name': 'Test',
            'email': 'test@example.com',
            'password': 'secret',
            'created_at': '2024-01-01T00:00:00'
        }
        
        # Include only specific fields
        include_serializer = APISerializer(include_fields=['id', 'name', 'email'])
        result = include_serializer.serialize(data)
        
        assert 'id' in result
        assert 'name' in result
        assert 'email' in result
        assert 'password' not in result
        assert 'created_at' not in result
        
        # Exclude specific fields
        exclude_serializer = APISerializer(exclude_fields=['password'])
        result = exclude_serializer.serialize(data)
        
        assert 'id' in result
        assert 'name' in result
        assert 'email' in result
        assert 'password' not in result
        assert 'created_at' in result
    
    def test_list_serialization(self):
        """Test serializing lists of objects."""
        serializer = APISerializer()
        
        data = [
            {'id': 1, 'name': 'Item 1'},
            {'id': 2, 'name': 'Item 2'},
            {'id': 3, 'name': 'Item 3'}
        ]
        
        result = serializer.serialize(data)
        
        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0]['id'] == 1
        assert result[1]['name'] == 'Item 2'


class TestAPIVersioning:
    """Test API versioning functionality."""
    
    def test_version_manager_setup(self):
        """Test setting up API version manager."""
        manager = APIVersionManager()
        
        # Register versions
        manager.register_version("v1", is_default=True)
        manager.register_version("v2")
        
        assert manager.default_version == "v1"
        assert "v1" in manager.versions
        assert "v2" in manager.versions
    
    def test_version_from_request(self):
        """Test extracting version from request."""
        manager = APIVersionManager()
        manager.register_version("v1", is_default=True)
        manager.register_version("v2")
        
        # Test header version
        mock_request = MagicMock()
        mock_request.headers = {'API-Version': 'v2'}
        mock_request.args = {}
        
        version = manager.get_version_from_request(mock_request)
        assert version == "v2"
        
        # Test query parameter version
        mock_request.headers = {}
        mock_request.args = {'version': 'v2'}
        
        version = manager.get_version_from_request(mock_request)
        assert version == "v2"
        
        # Test default version
        mock_request.headers = {}
        mock_request.args = {}
        
        version = manager.get_version_from_request(mock_request)
        assert version == "v1"
    
    def test_version_deprecation(self):
        """Test version deprecation."""
        manager = APIVersionManager()
        manager.register_version("v1")
        
        # Initially not deprecated
        assert not manager.is_version_deprecated("v1")
        
        # Deprecate version
        manager.deprecate_version("v1")
        assert manager.is_version_deprecated("v1")


class TestAPIModels:
    """Test API model validation."""
    
    def test_api_model_validation(self):
        """Test API model field validation."""
        class UserModel(APIModel):
            username: str = APIField(str, min_length=3, max_length=20)
            email: str = APIField(str, pattern=r'^[^@]+@[^@]+\.[^@]+$')
            age: int = APIField(int, min_value=0, max_value=120)
        
        # Valid data
        valid_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'age': 25
        }
        
        model = UserModel.from_dict(valid_data)
        assert model.username == 'testuser'
        assert model.email == 'test@example.com'
        assert model.age == 25
        
        # Invalid data - username too short
        invalid_data = {
            'username': 'ab',  # Too short
            'email': 'test@example.com',
            'age': 25
        }
        
        with pytest.raises(ValidationError):
            UserModel.from_dict(invalid_data)
    
    def test_api_field_validation(self):
        """Test individual API field validation."""
        # String length validation
        field = APIField(str, min_length=5, max_length=10)
        
        # Valid values should not raise
        APIModel._validate_field('test_field', 'hello', field)
        
        # Invalid values should raise
        with pytest.raises(ValidationError):
            APIModel._validate_field('test_field', 'hi', field)  # Too short
        
        with pytest.raises(ValidationError):
            APIModel._validate_field('test_field', 'this is too long', field)  # Too long
        
        # Numeric validation
        numeric_field = APIField(int, min_value=0, max_value=100)
        
        APIModel._validate_field('test_field', 50, numeric_field)
        
        with pytest.raises(ValidationError):
            APIModel._validate_field('test_field', -1, numeric_field)  # Too small
        
        with pytest.raises(ValidationError):
            APIModel._validate_field('test_field', 101, numeric_field)  # Too large


class TestErrorHandling:
    """Test API error handling."""
    
    def test_api_error_creation(self):
        """Test creating API errors."""
        error = APIError("Something went wrong", status_code=400)
        
        assert error.message == "Something went wrong"
        assert error.status_code == 400
        assert error.details == {}
    
    def test_validation_error(self):
        """Test validation error specifics."""
        error = ValidationError("Invalid field", field="email")
        
        assert error.message == "Invalid field"
        assert error.field == "email"
        assert error.status_code == 400
    
    def test_rate_limit_error(self):
        """Test rate limit error."""
        error = RateLimitError("Too many requests", retry_after=60)
        
        assert error.message == "Too many requests"
        assert error.retry_after == 60
        assert error.status_code == 429
    
    def test_error_response_creation(self):
        """Test creating standardized error responses."""
        # API Error
        api_error = APIError("Test error", status_code=400, details={'field': 'value'})
        response = create_error_response(api_error)
        
        assert response['error']['type'] == 'APIError'
        assert response['error']['message'] == 'Test error'
        assert response['error']['status_code'] == 400
        assert response['error']['details'] == {'field': 'value'}
        
        # Validation Error
        validation_error = ValidationError("Invalid email", field="email")
        response = create_error_response(validation_error)
        
        assert response['error']['type'] == 'ValidationError'
        assert response['error']['field'] == 'email'
        
        # Generic Exception
        generic_error = Exception("Something broke")
        response = create_error_response(generic_error)
        
        assert response['error']['type'] == 'Exception'
        assert response['error']['message'] == 'Something broke'
        assert response['error']['status_code'] == 500


class TestAPIFramework:
    """Test API Framework integration."""
    
    def setup_method(self):
        """Set up test API framework."""
        self.app = MagicMock()
        self.api = APIFramework(
            self.app,
            enable_rate_limiting=True,
            enable_versioning=True,
            default_pagination_size=10
        )
    
    def test_api_framework_initialization(self):
        """Test API framework initialization."""
        assert self.api.app == self.app
        assert self.api.enable_rate_limiting is True
        assert self.api.enable_versioning is True
        assert self.api.default_pagination_size == 10
        assert hasattr(self.api, 'rate_limiter')
        assert hasattr(self.api, 'version_manager')
    
    def test_convenience_decorators(self):
        """Test convenience HTTP method decorators."""
        # Test that decorators exist and are callable
        assert callable(self.api.get)
        assert callable(self.api.post)
        assert callable(self.api.put)
        assert callable(self.api.patch)
        assert callable(self.api.delete)
        assert callable(self.api.paginated_get)
    
    def test_client_id_generation(self):
        """Test client ID generation for rate limiting."""
        # Mock request with user
        mock_request = MagicMock()
        mock_request.user = MagicMock()
        mock_request.user.id = "user123"
        mock_request.remote_addr = "192.168.1.1"
        
        client_id = self.api._get_client_id(mock_request)
        assert client_id == "user:user123"
        
        # Mock request without user
        mock_request.user = None
        
        client_id = self.api._get_client_id(mock_request)
        assert client_id == "ip:192.168.1.1"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
