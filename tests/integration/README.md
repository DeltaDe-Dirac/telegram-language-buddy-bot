# Integration Tests

This directory contains integration tests for the Telegram Language Buddy Bot that test the full application stack including:

- Flask API endpoints
- PostgreSQL database operations
- Service dependencies (database, external APIs)

## Prerequisites

- Docker and Docker Compose
- Make (optional, but recommended)

## Quick Start

### Run All Tests (Unit + Integration)

```bash
make test
```

### Run Only Integration Tests

```bash
make test-integration
```

### Manual Steps

```bash
# Build the test environment
docker-compose -f docker-compose.test.yml build

# Run the integration tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# Clean up
docker-compose -f docker-compose.test.yml down -v --remove-orphans
```

## Test Structure

### `conftest.py`
Contains pytest fixtures that:
- Wait for PostgreSQL to be ready
- Wait for the Flask app to be ready
- Clean the database between tests
- Provide database sessions and Flask test clients

### Test Files

- `test_api_endpoints.py` - Tests Flask API endpoints
- `test_database_integration.py` - Tests database operations

## Environment Variables

The integration tests use these environment variables (set in `docker-compose.test.yml`):

- `DATABASE_URL` - PostgreSQL connection string
- `FLASK_ENV` - Set to 'testing'
- `TELEGRAM_BOT_TOKEN` - Test bot token
- `GOOGLE_APPLICATION_CREDENTIALS_JSON` - Test Google credentials

## Database Cleanup

The `clean_database` fixture automatically:
1. Drops all existing tables
2. Recreates the database schema
3. Ensures each test starts with a clean database

## Debugging

### View Logs

```bash
make logs-integration
```

### Access Running Containers

```bash
make debug-integration
```

### Quick Test Run (Skip Build)

If you've already built the images:

```bash
make quick-integration
```

## Test Coverage

Integration tests are marked with `@pytest.mark.integration` and can be run separately:

```bash
python -m pytest tests/ -m integration -v
```

## CI/CD Integration

The integration tests are designed to run in CI/CD pipelines and include:
- Health checks for service dependencies
- Proper cleanup between test runs
- Containerized environment for consistent testing
