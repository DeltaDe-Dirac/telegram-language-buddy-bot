# Deployment Configuration

This project is configured to run tests before deployment to prevent broken code from reaching production.

## How It Works

### Option 1: Heroku Postbuild Script (Recommended)
- **File**: `heroku-postbuild`
- **When**: Runs automatically after Heroku installs dependencies
- **What**: Executes all tests and fails deployment if any test fails
- **Database**: Uses in-memory SQLite for testing

### Option 2: GitHub Actions (Alternative)
- **File**: `.github/workflows/test-and-deploy.yml`
- **When**: Runs on push to main/develop branches and pull requests
- **What**: Runs tests in CI environment before deployment
- **Benefits**: Faster feedback, can block PRs if tests fail

## Setup Instructions

### For Heroku Postbuild Script:

1. **Deploy to Heroku**:
   ```bash
   git push heroku main
   ```

2. **Heroku will automatically**:
   - Install dependencies from `requirements.txt`
   - Run the `heroku-postbuild` script
   - Execute all tests
   - Deploy only if tests pass

### For GitHub Actions:

1. **Set up secrets in GitHub**:
   - `HEROKU_API_KEY`: Your Heroku API key
   - `HEROKU_APP_NAME`: Your Heroku app name
   - `HEROKU_EMAIL`: Your Heroku email

2. **Push to trigger workflow**:
   ```bash
   git push origin main
   ```

## Test Configuration

- **Test Database**: In-memory SQLite (configured in `tests/conftest.py`)
- **Environment**: `FLASK_ENV=testing`
- **Coverage**: Generated automatically
- **Output**: Verbose with short tracebacks

## Troubleshooting

### Tests Fail in Heroku
1. Check Heroku logs: `heroku logs --tail`
2. Run tests locally: `python -m pytest tests/ -v`
3. Fix failing tests
4. Commit and push again

### Database Issues
- Tests use in-memory SQLite, not production database
- No external dependencies required for tests
- Database is reset between tests

### Environment Variables
- `FLASK_ENV=testing` is set automatically
- `DATABASE_URL=sqlite:///:memory:` for tests
- Production environment variables are preserved

## Best Practices

1. **Always run tests locally** before pushing
2. **Use feature branches** for development
3. **Check test coverage** regularly
4. **Monitor deployment logs** for issues
5. **Set up alerts** for failed deployments
