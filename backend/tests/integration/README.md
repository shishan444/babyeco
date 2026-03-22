# Integration Testing Infrastructure

## Overview

This directory contains the integration testing infrastructure for the BabyEco backend API. The tests verify API contracts, database operations, and end-to-end workflows.

## File Structure

```
tests/integration/
├── __init__.py              # Package initialization with documentation
├── conftest.py              # Pytest fixtures and configuration
├── fixtures.py              # Test data factories
├── helpers.py               # Test utility functions
└── test_api_contract.py     # API contract tests
```

## Components

### 1. conftest.py - Test Configuration

Provides pytest fixtures for:
- **test_engine**: Session-scoped PostgreSQL database engine
- **db_session**: Isolated database session with transaction rollback
- **app**: FastAPI application with database dependency override
- **integration_client**: Async HTTP client for API testing
- **authenticated_client**: Pre-authenticated client with valid JWT token
- **auth_headers**: Dummy authorization headers

### 2. fixtures.py - Test Data Factories

Factory classes for creating test data:
- **UserFixtures**: Create parent users with phone/email
- **ChildFixtures**: Create child profiles with PIN authentication
- **TaskFixtures**: Create tasks (one-time, daily, weekly) with completions
- **PointsFixtures**: Create points transactions
- **SampleData**: Pre-defined sample data templates

### 3. helpers.py - Test Utilities

Helper classes for common operations:
- **ClientHelper**: Create configured test clients
- **DataHelper**: Efficient test data setup
- **AuthHelper**: Authentication and token creation
- **CleanupHelper**: Test data cleanup operations
- **AssertionHelper**: Reusable test assertions

### 4. test_api_contract.py - API Contract Tests

Tests for authentication endpoints:
- **POST /api/v1/auth/register**: User registration
- **POST /api/v1/auth/login**: User login
- **POST /api/v1/auth/refresh**: Token refresh
- **GET /api/v1/auth/me**: Get current user
- **PATCH /api/v1/auth/me**: Update user profile
- **Error responses**: Standard error format validation

## Running Tests

### Run all integration tests
```bash
pytest tests/integration/ -v
```

### Run specific test file
```bash
pytest tests/integration/test_api_contract.py -v
```

### Run with coverage
```bash
pytest tests/integration/ --cov=app --cov-report=html
```

### Run with database output
```bash
pytest tests/integration/ -v -s
```

## CI/CD Integration

Tests run automatically on:
- Push to main, develop, feature/*, fix/* branches
- Pull requests to main or develop branches

The CI workflow:
1. Starts PostgreSQL and Redis services
2. Checks code formatting with ruff
3. Runs type checking with mypy
4. Runs unit tests with coverage
5. Runs integration tests with coverage
6. Uploads coverage reports

## Test Database

Integration tests use PostgreSQL test database:
- **Database**: babyeco_test
- **User**: postgres
- **Password**: postgres
- **Isolation**: Transaction rollback between tests

## Environment Variables

Required for integration tests:
```bash
TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/babyeco_test
```

## Writing New Integration Tests

### Example: Test new endpoint

```python
class TestNewEndpointContract:
    """Tests for POST /api/v1/new-endpoint contract."""

    async def test_success_contract(
        self,
        integration_client: AsyncClient,
    ) -> None:
        """Test successful response matches contract."""
        response = await integration_client.post(
            "/new-endpoint",
            json={"key": "value"},
        )

        assert response.status_code == 201
        data = response.json()
        assert "required_field" in data

    async def test_error_contract(
        self,
        integration_client: AsyncClient,
    ) -> None:
        """Test error response follows standard format."""
        response = await integration_client.post(
            "/new-endpoint",
            json={"invalid": "data"},
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
```

### Using test fixtures

```python
async def test_with_fixtures(
    integration_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Test using test data fixtures."""
    # Create test user
    user = await UserFixtures.create_parent(db=db, phone="+8613812345678")

    # Create test child
    child = await ChildFixtures.create_child(
        db=db,
        parent_id=user.id,
        name="Test Child",
    )

    # Test API with created data
    response = await integration_client.get(f"/children/{child.id}")
    assert response.status_code == 200
```

### Using helpers

```python
async def test_with_helpers(integration_client: AsyncClient) -> None:
    """Test using helper utilities."""
    # Register and login
    user_data, token = await AuthHelper.register_and_login(integration_client)

    # Create authenticated client
    headers = AuthHelper.create_auth_headers(user_id=1)

    # Test authenticated endpoint
    response = await integration_client.get("/auth/me", headers=headers)
    assert response.status_code == 200
```

## Best Practices

1. **Isolation**: Each test should be independent. Use transaction rollback for cleanup.
2. **Clarity**: Test names should describe what is being tested.
3. **Contracts**: Test both success and error cases for API contracts.
4. **Fixtures**: Use fixtures for common test data setup.
5. **Async**: Always use async/await for database and HTTP operations.
6. **Coverage**: Aim for 85%+ code coverage for integration tests.

## @MX Tag Usage

Integration tests use @MX tags for important context:
- `@MX:ANCHOR`: Key fixtures and helpers used across many tests
- `@MX:NOTE`: Implementation details and usage patterns
- `@MX:WARN`: Destructive operations or test isolation concerns

## Troubleshooting

### Database connection errors
```bash
# Check PostgreSQL is running on port 5432
docker ps | grep postgres

# Verify test database exists
psql -U postgres -h localhost -l
```

### Test isolation failures
```bash
# Run tests in isolation (one at a time)
pytest tests/integration/ --forked

# Check for missing rollbacks
pytest tests/integration/ -v -s | grep -i rollback
```

### Coverage issues
```bash
# Generate detailed coverage report
pytest tests/integration/ --cov=app --cov-report=html
open htmlcov/index.html
```

## Next Steps

1. Add contract tests for remaining API endpoints:
   - Children management (POST /children, GET /children/{id})
   - Tasks management (POST /tasks, PATCH /tasks/{id})
   - Points transactions (GET /points/history)
   - Rewards redemption (POST /rewards/{id}/redeem)

2. Add end-to-end workflow tests:
   - Complete task → Earn points → Redeem reward
   - Parent creates child → Child logs in → Completes task
   - Recurring task generation and completion

3. Add performance tests:
   - Bulk task creation
   - Points transaction history pagination
   - Multiple children per parent

4. Add security tests:
   - SQL injection attempts
   - XSS in user input
   - CSRF token validation
