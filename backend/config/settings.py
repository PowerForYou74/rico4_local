"""
ENV-System mit Load-Order und Source-Tracking
.env.local ≻ .env mit ENV_SOURCE tracking
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with ENV source tracking"""
    
    # ENV Source tracking
    env_source: str = Field(default="default", description="Source of environment variables")
    
    # API Keys
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    perplexity_api_key: Optional[str] = Field(default=None, env="PERPLEXITY_API_KEY")
    
    # Application settings
    app_name: str = Field(default="Rico Orchestrator", env="APP_NAME")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # API Settings
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    
    # Provider Settings
    default_provider: str = Field(default="openai", env="DEFAULT_PROVIDER")
    auto_race_timeout: float = Field(default=30.0, env="AUTO_RACE_TIMEOUT")
    
    # n8n Integration
    n8n_webhook_url: Optional[str] = Field(default=None, env="N8N_WEBHOOK_URL")
    n8n_api_key: Optional[str] = Field(default=None, env="N8N_API_KEY")
    
    model_config = {
        "env_file": (".env.local", ".env"),
        "env_file_encoding": "utf-8",
        "case_sensitive": False
    }


def _detect_env_source() -> str:
    """Detect which environment file is being used"""
    if os.path.exists(".env.local"):
        return ".env.local"
    if os.path.exists(".env"):
        return ".env"
    return "environment"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance with proper ENV source detection"""
    settings = Settings()
    settings.env_source = _detect_env_source()
    return settings


# Global settings instance
settings = get_settings()
