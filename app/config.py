"""Application configuration using Pydantic."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    # App
    app_env: str = "development"
    debug: bool = True
    
    # Database
    database_url: str = "sqlite:///data/news.db"
    
    # News collection
    news_scan_interval: int = 3600  # seconds
    
    # Scoring thresholds
    # MVP accepts single-source stories; raise this after verification is added.
    min_confidence: float = 0.50
    # MVP keeps a broad shortlist; tighten this after richer topic signals exist.
    min_insolite_score: float = 0.35
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def database_path(self) -> str:
        """Extract database path from URL."""
        if self.database_url.startswith("sqlite:///"):
            return self.database_url.replace("sqlite:///", "")
        return self.database_url

    @property
    def db_dir(self) -> Path:
        """Get database directory."""
        db_path = Path(self.database_path)
        return db_path.parent


settings = Settings()

# Ensure data directory exists
if "sqlite" in settings.database_url:
    settings.db_dir.mkdir(parents=True, exist_ok=True)
