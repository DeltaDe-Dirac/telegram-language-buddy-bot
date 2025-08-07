# Test Suite for Telegram Language Buddy Bot

This directory contains comprehensive unit tests and integration tests for the Telegram Language Buddy Bot to ensure code quality and prevent regressions.

## Test Structure

### Unit Tests

- **`test_language_detector.py`** - Tests for `LanguageDetector` class
  - Language validation
  - Language list formatting
  - Supported languages integrity

- **`test_free_translator.py`** - Tests for `FreeTranslator` class
  - Translation functionality (with mocking)
  - Language detection
  - Error handling
  - Input validation

- **`test_database.py`** - Tests for `DatabaseManager` class
  - User preferences CRUD operations
  - User statistics management
  - Language selection state management
  - Message translation storage
  - Database session management

- **`test_telegram_bot.py`** - Tests for `TelegramBot` class
  - Bot initialization
  - Message sending/receiving
  - Language pair management
  - Command handling
  - Keyboard creation
  - Error handling

- **`test_bot_controller.py`** - Tests for controller functions
  - Webhook handling
  - API endpoints
  - Request processing
  - Response formatting
  - Singleton pattern

### Integration Tests

- **`test_integration.py`** - Tests component interactions
  - Bot-database integration
  - Bot-translator integration
  - Complete workflows
  - Error handling across components
  - Concurrent user management

## Running Tests

### Run All Tests
```bash
python tests/run_tests.py
```

### Run Specific Test Module
```bash
python -m unittest tests.test_language_detector
python -m unittest tests.test_database
```

### Run Specific Test Class
```bash
python tests/run_tests.py tests.test_language_detector.TestLanguageDetector
```

### Run Specific Test Method
```bash
python tests/run_tests.py tests.test_language_detector.TestLanguageDetector.test_is_valid_language_valid_codes
```

### Run with Coverage (if coverage.py is installed)
```bash
coverage run tests/run_tests.py
coverage report
coverage html  # Generate HTML report
```

## Test Configuration

### Environment Setup
Tests use in-memory SQLite databases to avoid affecting production data. Environment variables are mocked where needed.

### Mocking Strategy
- **External APIs**: Telegram API calls are mocked using `unittest.mock`
- **Translation Services**: Google Translate calls are mocked to avoid rate limits
- **Database**: Uses in-memory SQLite for isolation
- **Environment Variables**: Mocked for consistent test environment

### Test Data
- Uses realistic but safe test data
- No real API keys or tokens
- Isolated test databases

## Test Coverage

The test suite covers:

### Core Functionality
- ✅ Language detection and validation
- ✅ Translation services
- ✅ Database operations
- ✅ Telegram Bot API integration
- ✅ Webhook processing
- ✅ User preference management

### Edge Cases
- ✅ Invalid inputs
- ✅ Network failures
- ✅ Database errors
- ✅ API rate limits
- ✅ Malformed requests

### Integration Scenarios
- ✅ Complete user workflows
- ✅ Multi-user scenarios
- ✅ Error propagation
- ✅ State management

## Best Practices

### Writing New Tests
1. **Follow naming convention**: `test_<method_name>_<scenario>`
2. **Use descriptive test names**: Clear what is being tested
3. **Test one thing per test**: Single responsibility principle
4. **Use appropriate assertions**: Specific assertions for better error messages
5. **Mock external dependencies**: Avoid real API calls
6. **Clean up resources**: Use `tearDown` methods

### Test Organization
```python
class TestClassName(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        pass
    
    def test_method_name_success(self):
        """Test successful scenario"""
        pass
    
    def test_method_name_failure(self):
        """Test failure scenario"""
        pass
    
    def test_method_name_edge_case(self):
        """Test edge case"""
        pass
    
    def tearDown(self):
        """Clean up after tests"""
        pass
```

### Mocking Guidelines
```python
# Mock external dependencies
@patch('module.external_service')
def test_method(self, mock_service):
    mock_service.return_value = expected_result
    # Test code here
    mock_service.assert_called_once_with(expected_args)

# Mock environment variables
@patch.dict('os.environ', {'KEY': 'value'})
def test_method(self):
    # Test code here
    pass
```

## Continuous Integration

### Pre-commit Checklist
- [ ] All tests pass
- [ ] No new warnings
- [ ] Code coverage maintained or improved
- [ ] Documentation updated

### CI Pipeline
Tests should be run automatically on:
- Pull requests
- Code merges
- Release builds

## Troubleshooting

### Common Issues

**Import Errors**
- Ensure `src` directory is in Python path
- Check module imports in test files

**Database Errors**
- Tests use in-memory SQLite
- Ensure proper cleanup in `tearDown`

**Mock Issues**
- Verify mock paths match actual import paths
- Check mock setup in test methods

**Environment Issues**
- Tests mock environment variables
- No real API keys needed

### Debug Mode
Run tests with increased verbosity:
```bash
python -m unittest -v tests.test_module
```

## Performance

### Test Execution Time
- Unit tests: ~1-2 seconds
- Integration tests: ~3-5 seconds
- Full suite: ~5-10 seconds

### Optimization Tips
- Use in-memory databases
- Mock external services
- Minimize file I/O
- Use appropriate test isolation

## Contributing

When adding new features:
1. Write tests first (TDD approach)
2. Ensure all existing tests pass
3. Add integration tests for new workflows
4. Update this documentation if needed

When fixing bugs:
1. Write a test that reproduces the bug
2. Fix the bug
3. Ensure the test passes
4. Run full test suite
