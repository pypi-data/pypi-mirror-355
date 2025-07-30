"""Configuration management for the application."""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

def find_env_file() -> str:
    """Find the .env file by looking in the current directory and package root."""
    # Current working directory
    if os.path.exists(".env"):
        return ".env"
    
    # Package root directory
    package_root = Path(__file__).parent.parent
    env_path = package_root / ".env"
    if env_path.exists():
        return str(env_path)
    
    # Example.env in package root
    example_env = package_root / "example.env"
    if example_env.exists():
        return str(example_env)
    
    return ".env"  # Default to local .env even if it doesn't exist

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    GITHUB_TOKEN: Optional[str] = None
    PORT: int = 5043
    HOST: str = "0.0.0.0"
    DEBUG: bool = False
    TEMP_DIR: str = os.path.join(os.path.expanduser("~"), ".test-impact-analyzer")

    class Config:
        env_file = find_env_file()
        case_sensitive = True

settings = Settings()
