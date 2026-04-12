# core/config.py

import os
from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

_DEFAULT_EXECUTION_BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

class Settings(BaseSettings):
    """
    Application configuration settings
    """
    # API Configuration
    app_name: str = "AI Terminal Backend"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8001
    
    # Gemini AI Configuration
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    ai_timeout_seconds: int = int(os.getenv("AI_TIMEOUT_SECONDS", "60"))
    
    # Security Configuration
    allow_destructive_commands: bool = False
    max_command_length: int = 500
    execution_base_dir: str = os.getenv("EXECUTION_BASE_DIR", _DEFAULT_EXECUTION_BASE_DIR)
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    """
    return Settings()
