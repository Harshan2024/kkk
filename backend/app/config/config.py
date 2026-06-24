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
    
    # Environment mode (development/production)
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # PostgreSQL Database URL
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@localhost:5432/carbontracker"
    )
    
    # Authentication & JWT Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super_secret_carbontracker_development_key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
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

def validate_environment_on_startup():
    """
    Validates required environment variables and outputs warnings if any are missing.
    Never crashes the application startup.
    """
    import sys
    import logging
    logger = logging.getLogger("carbontracker.config")
    
    vars_to_check = {
        "DATABASE_URL": (os.getenv("DATABASE_URL"), "Database services disabled."),
        "SECRET_KEY": (os.getenv("SECRET_KEY"), "Authentication services disabled."),
        "OPENAI_API_KEY": (os.getenv("OPENAI_API_KEY"), "AI services disabled."),
        "ENVIRONMENT": (os.getenv("ENVIRONMENT"), "Environment mode defaults to development.")
    }
    
    has_missing = False
    for var_name, (var_val, service_desc) in vars_to_check.items():
        if not var_val:
            # Construct exact warning block
            warning_msg = f"\nWARNING\n\n{var_name} missing.\n\n{service_desc}\n"
            # Print to stdout/stderr
            print(warning_msg, file=sys.stderr, flush=True)
            # Log structured warning
            logger.warning(f"{var_name} missing. {service_desc}")
            has_missing = True
            
    if not has_missing:
        logger.info("All required environment variables verified successfully.")


