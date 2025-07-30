"""Runner script for the Test Impact Analyzer application."""
import os
import sys
from pathlib import Path

# Add the src directory to Python path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.append(src_path)

from app import app
from config import settings
from utils.logging import logger

# Ensure temp directory exists
Path(settings.TEMP_DIR).mkdir(parents=True, exist_ok=True)

# Load environment variables from .env file if it exists
env_file = Path(".env")
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv()

def main():
    """Run the application."""
    logger.info(f"Starting Test Impact Analyzer on {settings.HOST}:{settings.PORT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Temporary directory: {settings.TEMP_DIR}")
    
    if not os.environ.get("GITHUB_TOKEN"):
        logger.warning("GITHUB_TOKEN not set - GitHub integration will be limited")
    
    try:
        app.run(
            host=settings.HOST,
            port=settings.PORT,
            debug=settings.DEBUG
        )
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
