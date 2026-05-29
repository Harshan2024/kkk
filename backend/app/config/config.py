import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the backend project (three levels up from backend/app/config/config.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = BASE_DIR / ".env"

# Explicitly load .env with absolute path mapping
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv() # Fallback walking search

class Settings:
    PROJECT_NAME: str = "CarbonTracker API"
    API_V1_STR: str = "/api/v1"
    
    # PostgreSQL Database URL
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@localhost:5432/carbontracker"
    )
    
    # CORS settings (supporting both localhost and 127.0.0.1 on ports 3000 and 3001)
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
    ]
    
    # NLP Configuration
    SPACY_MODEL: str = "en_core_web_sm"

settings = Settings()
