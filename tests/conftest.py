import os
import pytest
import tempfile
from src.models.database import DatabaseManager, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="session")
def test_database():
    """Create a test database for the test session"""
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    # Create session factory
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Override the database manager's engine
    original_engine = DatabaseManager.engine
    DatabaseManager.engine = engine
    DatabaseManager.SessionLocal = TestingSessionLocal
    
    yield engine
    
    # Restore original engine
    DatabaseManager.engine = original_engine

@pytest.fixture(autouse=True)
def setup_test_env(test_database):
    """Set up test environment before each test"""
    # Set test environment variables
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    
    yield
    
    # Clean up after each test
    with DatabaseManager.get_session() as session:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()

@pytest.fixture
def mock_telegram_token():
    """Mock Telegram bot token for tests"""
    return "test_token_12345"

@pytest.fixture
def mock_webhook_url():
    """Mock webhook URL for tests"""
    return "https://example.com/webhook"
