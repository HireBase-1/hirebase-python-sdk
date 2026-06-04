"""Configuration management for Hirebase CLI."""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

DEFAULT_API_URL = "https://api.hirebase.org"


@dataclass
class Config:
    """Configuration for the Hirebase CLI."""
    
    api_url: str
    api_key: str
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        load_dotenv()
        
        api_url = (
            os.getenv("HIREBASE_BASE_URL")
            or os.getenv("HIREBASE_API_URL")
            or DEFAULT_API_URL
        )
        api_key = os.getenv("HIREBASE_API_KEY")
        
        if not api_key:
            raise ConfigError("HIREBASE_API_KEY environment variable is not set")
        
        api_url = api_url.rstrip("/")
        
        return cls(api_url=api_url, api_key=api_key)
    
    @classmethod
    def from_env_optional(cls) -> Optional["Config"]:
        """Load configuration from environment variables, returning None if not set."""
        try:
            return cls.from_env()
        except ConfigError:
            return None


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


def get_config() -> Config:
    """Get the current configuration."""
    return Config.from_env()
