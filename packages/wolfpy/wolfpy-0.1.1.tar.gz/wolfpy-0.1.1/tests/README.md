# WolfPy Framework Test Suite

This directory contains the comprehensive test suite for the WolfPy Framework, covering all enhanced features across phases 4, 5, and 6.

## Test Structure

### Core Test Files

- **`test_auth.py`** - Authentication system tests
  - User management and profiles
  - Password security and policies
  - JWT token authentication
  - Multi-factor authentication (MFA)
  - Role-based access control
  - Authentication decorators

- **`test_database.py`** - Database ORM tests
  - Field types and validation
  - Model definition and operations
  - Advanced QuerySet functionality
  - Relationships (Foreign Key, Many-to-Many)
  - Query filtering and ordering
  - Model managers and bulk operations

- **`test_api.py`** - REST API system tests
  - Pagination and serialization
  - Rate limiting and throttling
  - API versioning
  - Error handling and responses
  - Request/response validation
  - API framework integration

- **`test_core.py`** - Core framework tests
  - Application setup and configuration
  - Request and response handling
  - Routing and URL patterns
  - Template rendering
  - Basic WSGI functionality

- **`test_integration.py`** - End-to-end integration tests
  - Complete authentication workflows
  - Database + API integration
  - Full request/response cycles
  - Error handling scenarios

### Configuration Files

- **`conftest.py`** - Pytest configuration and shared fixtures
- **`pytest.ini`** - Pytest settings and markers
- **`README.md`** - This documentation file

## Running Tests

### Quick Start

```bash
# Run all tests
python run_tests.py

# Run with coverage
python run_tests.py --coverage

# Run specific test categories
python run_tests.py --auth      # Authentication tests
python run_tests.py --database  # Database tests
python run_tests.py --api       # API tests
python run_tests.py --integration # Integration tests

# Run fast tests only (skip slow tests)
python run_tests.py --fast

# Run with verbose output
python run_tests.py --verbose
```

### Using Pytest Directly

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest tests/ --cov=src/wolfpy --cov-report=html

# Run tests with specific markers
pytest tests/ -m "auth"
pytest tests/ -m "not slow"
pytest tests/ -m "database and not integration"

# Run with verbose output
pytest tests/ -v

# Run specific test method
pytest tests/test_auth.py::TestUserManagement::test_create_user
```

## Test Categories and Markers

### Markers

- **`@pytest.mark.auth`** - Authentication-related tests
- **`@pytest.mark.database`** - Database and ORM tests
- **`@pytest.mark.api`** - API functionality tests
- **`@pytest.mark.integration`** - End-to-end integration tests
- **`@pytest.mark.slow`** - Tests that take longer to run
- **`@pytest.mark.unit`** - Unit tests (isolated components)
- **`@pytest.mark.functional`** - Functional tests (feature workflows)

### Test Categories

#### Authentication Tests (`test_auth.py`)
- User creation and management
- Password hashing and validation
- JWT token creation and verification
- MFA setup and verification
- Role and permission management
- Authentication decorators
- Account security features

#### Database Tests (`test_database.py`)
- Field type validation
- Model CRUD operations
- QuerySet filtering and ordering
- Relationship handling
- Query optimization
- Bulk operations
- Model validation

#### API Tests (`test_api.py`)
- Pagination functionality
- Rate limiting
- Serialization and deserialization
- API versioning
- Error response formatting
- Request validation
- Response handling

#### Core Tests (`test_core.py`)
- Application initialization
- Request parsing
- Response creation
- Routing and URL matching
- Template rendering
- Static file handling

#### Integration Tests (`test_integration.py`)
- Complete user workflows
- Authentication + API integration
- Database + API integration
- Error handling scenarios
- End-to-end request cycles

## Test Dependencies

### Required Dependencies
- `pytest` - Test framework
- `unittest.mock` - Mocking utilities (built-in)

### Optional Dependencies
- `pytest-cov` - Coverage reporting
- `pytest-xdist` - Parallel test execution
- `pytest-benchmark` - Performance benchmarking
- `PyJWT` - JWT token support (enables JWT tests)
- `pyotp` - MFA support (enables MFA tests)
- `bcrypt` - Enhanced password hashing (enables bcrypt tests)

### Installing Test Dependencies

```bash
# Install required dependencies
pip install pytest

# Install optional dependencies
pip install pytest-cov pytest-xdist pytest-benchmark

# Install WolfPy optional features
pip install PyJWT pyotp bcrypt
```

## Test Data and Fixtures

### Shared Fixtures (in `conftest.py`)
- `temp_db` - Temporary database file
- `temp_dir` - Temporary directory
- `mock_request` - Mock HTTP request
- `sample_user_data` - Sample user data
- `sample_post_data` - Sample post data
- `test_client` - Test client factory
- `auth_with_test_user` - Auth system with test user
- `db_with_sample_data` - Database with sample data

### Test Utilities
- `TestClient` - Simple HTTP client for testing
- `Timer` - Performance benchmarking utility

## Coverage Reporting

### Generate Coverage Report

```bash
# HTML coverage report
python run_tests.py --coverage

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Coverage Targets
- **Overall Coverage**: > 90%
- **Core Modules**: > 95%
- **Authentication**: > 95%
- **Database ORM**: > 90%
- **API Framework**: > 90%

## Performance Testing

### Benchmark Tests
Some tests include performance benchmarks to ensure the framework maintains good performance:

```bash
# Run with benchmark plugin
pytest tests/ --benchmark-only
```

### Performance Targets
- **Request handling**: < 10ms per request
- **Database queries**: < 5ms per simple query
- **Authentication**: < 50ms per login
- **Template rendering**: < 20ms per template

## Continuous Integration

### GitHub Actions
The test suite is designed to run in CI environments:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements-test.txt
    python run_tests.py --coverage
```

### Test Matrix
Tests are run against:
- Python 3.8, 3.9, 3.10, 3.11, 3.12
- With and without optional dependencies
- Different operating systems (Linux, macOS, Windows)

## Writing New Tests

### Test Structure
```python
class TestFeatureName:
    """Test feature description."""
    
    def setup_method(self):
        """Set up test environment."""
        pass
    
    def teardown_method(self):
        """Clean up after tests."""
        pass
    
    def test_specific_functionality(self):
        """Test specific functionality."""
        # Arrange
        # Act
        # Assert
        pass
```

### Best Practices
1. Use descriptive test names
2. Follow Arrange-Act-Assert pattern
3. Use appropriate fixtures
4. Add markers for categorization
5. Clean up resources in teardown
6. Test both success and failure cases
7. Use mocks for external dependencies

### Adding New Test Categories
1. Create new test file: `test_feature.py`
2. Add marker in `pytest.ini`
3. Update `conftest.py` if needed
4. Add to test runner options
5. Update this documentation

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `src/` is in Python path
2. **Database Errors**: Check temporary file permissions
3. **Missing Dependencies**: Install optional packages
4. **Slow Tests**: Use `--fast` flag to skip slow tests
5. **Permission Errors**: Check file system permissions

### Debug Mode
```bash
# Run with debug output
pytest tests/ -s --tb=long

# Run single test with debug
pytest tests/test_auth.py::TestUserManagement::test_create_user -s -vv
```

### Getting Help
- Check test output for specific error messages
- Review fixture setup in `conftest.py`
- Ensure all dependencies are installed
- Check Python path and imports
- Review test isolation and cleanup
