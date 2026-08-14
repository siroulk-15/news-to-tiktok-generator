"""Pytest configuration and fixtures."""

import os
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, NewsArticleDB, StoryDB, NewsSourceDB
from app.config import Settings


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for testing."""
    # Create temporary database file
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(bind=engine)
    
    yield SessionLocal(), engine, db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def db_session(temp_db):
    """Get database session."""
    session, engine, path = temp_db
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def test_settings(monkeypatch, temp_db):
    """Override settings for testing."""
    _, _, db_path = temp_db
    
    settings = Settings(
        app_env="test",
        database_url=f"sqlite:///{db_path}",
        debug=False
    )
    
    return settings
