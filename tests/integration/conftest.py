"""
Integration test configuration - simplified for Docker environment
"""
import pytest
import os
import time
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Set up module path
import sys
sys.path.insert(0, '/app')


def get_database_url():
    """Get database URL from environment"""
    return os.environ.get(
        'DATABASE_URL',
        'postgresql://test_user:test_password@postgres:5432/test_db'
    )


@pytest.fixture(scope="session")
def postgres_engine():
    """Create PostgreSQL engine and wait for it to be ready"""
    database_url = get_database_url()
    print(f"\n🔗 Connecting to database: {database_url}")
    
    for attempt in range(30):
        try:
            engine = create_engine(database_url, echo=False)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"✅ PostgreSQL is ready!")
            return engine
        except Exception as e:
            print(f"⏳ Waiting for PostgreSQL (attempt {attempt + 1}/30): {e}")
            time.sleep(2)
    
    raise Exception("PostgreSQL failed to start within timeout")


@pytest.fixture(scope="session")
def app_ready():
    """Wait for the Flask app to be ready"""
    app_url = os.environ.get("APP_URL", "http://app:5000/")
    print(f"\n🔗 Checking Flask app at: {app_url}")
    
    for attempt in range(30):
        try:
            response = requests.get(app_url, timeout=5)
            if response.status_code == 200:
                print("✅ Flask app is ready!")
                return True
        except Exception as e:
            print(f"⏳ Waiting for Flask app (attempt {attempt + 1}/30): {e}")
            time.sleep(2)
    
    raise Exception("Flask app failed to start within timeout")


@pytest.fixture(scope="function")
def db_session(postgres_engine):
    """Provide a database session for testing"""
    print("\n📊 Setting up db_session fixture...")
    
    # Import here to avoid import issues at module level
    from src.models.database import Base
    
    # Create all tables
    Base.metadata.create_all(bind=postgres_engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=postgres_engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Clean up tables after each test
        Base.metadata.drop_all(bind=postgres_engine)


@pytest.fixture
def client(app_ready):
    """Provide a test client for the Flask app"""
    print("\n🧪 Setting up test client fixture...")
    
    from src.main import app
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client
