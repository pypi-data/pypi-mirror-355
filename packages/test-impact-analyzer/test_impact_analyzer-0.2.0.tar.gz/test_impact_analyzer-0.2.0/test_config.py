from src.config import settings
import os

print("Current working directory:", os.getcwd())
print("Contents of .env file:")
try:
    with open(".env") as f:
        print(f.read())
except FileNotFoundError:
    print(".env file not found")
except Exception as e:
    print(f"Error reading .env: {e}")

print("\nEnvironment variables loaded:")
print(f"GITHUB_TOKEN: {'set' if settings.GITHUB_TOKEN else 'not set'}")
print(f"PORT: {settings.PORT}")
print(f"HOST: {settings.HOST}")
print(f"DEBUG: {settings.DEBUG}")
print(f"TEMP_DIR: {settings.TEMP_DIR}")
