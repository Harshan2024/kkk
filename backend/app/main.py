import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config.config import settings
from app.api.endpoints import router as api_router
from app.database.session import engine, SessionLocal, Base, verify_database_connection, sync_database_schema
from app.emissions.factors import seed_db
from app.logging.logger import configure_logging
from app.logging.error_logger import setup_error_logging

# Configure application logging
configure_logging()
logger = logging.getLogger("carbontracker.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions: Verify PostgreSQL connectivity and set up schemas
    logger.info("Initializing CarbonTracker Backend lifespan...")
    
    # Run the connection verification loop (retry 5 times, delay 2 seconds)
    db_connected = verify_database_connection(retries=5, delay=2.0)
    
    if db_connected:
        try:
            logger.info("Running database schema synchronization...")
            # Create tables that don't exist
            Base.metadata.create_all(bind=engine)
            # Sync new columns dynamically for existing tables (Phase-3 compatibility)
            sync_database_schema(engine)
            logger.info(">>> Database schema synchronization completed.")
        except Exception as e:
            logger.error(f"Error during schema synchronization: {str(e)}")
    else:
        logger.error(
            "!!! PostgreSQL Database is unreachable. The application will start in database-offline mode. "
            "Typing parser previews will still work using static configurations, but logs cannot be saved. "
            "Please configure your DATABASE_URL in backend/.env"
        )
    yield
    # Shutdown actions

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Register global centralized exception logger middleware
setup_error_logging(app)


# CORS middleware configuration
# Supports all standard local ports (3000, 3001) for both localhost and 127.0.0.1 loopbacks
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API endpoints
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(api_router, prefix="/api")

@app.get("/health")
@app.get("/api/health")
def health_check():
    """
    Detailed health check validating server running, database connected, and statistics API working.
    """
    db_status = "disconnected"
    stats_status = "error"
    
    try:
        # Open a short-lived test connection
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            db_status = "connected"
            
            # Query the Activity table to ensure stats aggregates can run
            from app.models import Activity
            db.query(Activity).count()
            stats_status = "working"
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Health check failed validation checks: {str(e)}")
        
    return {
        "backend": "running",
        "database": db_status,
        "statistics_api": stats_status
    }

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the CarbonTracker API",
        "status": "online",
        "version": "1.0.0"
    }
