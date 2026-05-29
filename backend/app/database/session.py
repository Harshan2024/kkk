import time
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("carbontracker.database")

# Startup database validation
if not settings.DATABASE_URL:
    logger.critical("DATABASE_URL is not set! The backend cannot function without a database connection string.")
    raise ValueError("Configuration Error: DATABASE_URL environment variable is missing.")

# Create SQLAlchemy engine with resilient connection pooling parameters
# pool_recycle: Recycles connections older than 5 minutes (prevents serverless dropouts)
# pool_pre_ping: Checks if connection is alive before serving a query
# pool_timeout: Limits thread waiting to 15 seconds
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=15,
    max_overflow=25,
    pool_recycle=300,
    pool_timeout=15
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def verify_database_connection(retries: int = 5, delay: float = 2.0) -> bool:
    """
    Attempts to connect to the database with a retry loop.
    Returns True if connection is verified, False otherwise.
    """
    logger.info(f"Verifying PostgreSQL database connection (Retries: {retries})...")
    for attempt in range(1, retries + 1):
        try:
            # Try to connect and execute a lightweight test query
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                conn.commit()
            logger.info(">>> PostgreSQL Database connection verified successfully.")
            return True
        except Exception as e:
            logger.warning(
                f"Database connection attempt {attempt}/{retries} failed. "
                f"Retrying in {delay} seconds... Error details: {str(e)}"
            )
            time.sleep(delay)
            
    logger.critical("!!! Database connection verification failed after all retries.")
    return False

def get_db():
    """
    Dependency generator for FastAPI routes.
    Automatically closes session after processing requests.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def sync_database_schema(engine) -> None:
    """
    Verifies and adds missing columns for Phase-3 models dynamically.
    Helps sync schemas on PostgreSQL/SQLite without dropping existing table data.
    """
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    
    # 1. Check table "chat_messages"
    if "chat_messages" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("chat_messages")]
        
        with engine.connect() as conn:
            # 1.1 embedding_id
            if "embedding_id" not in columns:
                logger.info("Adding missing column 'embedding_id' to table 'chat_messages'...")
                try:
                    conn.execute(text("ALTER TABLE chat_messages ADD COLUMN embedding_id VARCHAR(500) NULL"))
                    conn.commit()
                except Exception as e:
                    logger.error(f"Failed to add column 'embedding_id': {str(e)}")
                    
            # 1.2 semantic_summary
            if "semantic_summary" not in columns:
                logger.info("Adding missing column 'semantic_summary' to table 'chat_messages'...")
                try:
                    conn.execute(text("ALTER TABLE chat_messages ADD COLUMN semantic_summary VARCHAR(1000) NULL"))
                    conn.commit()
                except Exception as e:
                    logger.error(f"Failed to add column 'semantic_summary': {str(e)}")
                    
            # 1.3 context_tags
            if "context_tags" not in columns:
                logger.info("Adding missing column 'context_tags' to table 'chat_messages'...")
                try:
                    conn.execute(text("ALTER TABLE chat_messages ADD COLUMN context_tags JSON NULL"))
                    conn.commit()
                except Exception as e:
                    try:
                        conn.execute(text("ALTER TABLE chat_messages ADD COLUMN context_tags TEXT NULL"))
                        conn.commit()
                    except Exception as e2:
                        logger.error(f"Failed to add context_tags column fallback: {str(e2)}")

    # 2. Check table "ai_insights"
    if "ai_insights" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("ai_insights")]
        
        with engine.connect() as conn:
            db_driver = engine.url.drivername
            is_postgres = "postgres" in db_driver or "psycopg" in db_driver
            
            float_type = "DOUBLE PRECISION" if is_postgres else "FLOAT"
            text_type = "VARCHAR(2000)"
            
            new_cols = {
                "impact_value": f"{float_type} NULL",
                "feasibility": "VARCHAR(50) NULL",
                "difficulty": "VARCHAR(50) NULL",
                "confidence_score": f"{float_type} NULL",
                "sustainability_gain": f"{float_type} NULL",
                "behavioral_compatibility": f"{float_type} NULL",
                "why_explanation": f"{text_type} NULL",
                "how_calculation": f"{text_type} NULL",
                "weighted_priority_score": f"{float_type} NULL"
            }
            
            for col_name, col_sql in new_cols.items():
                if col_name not in columns:
                    logger.info(f"Adding missing column '{col_name}' to table 'ai_insights'...")
                    try:
                        conn.execute(text(f"ALTER TABLE ai_insights ADD COLUMN {col_name} {col_sql}"))
                        conn.commit()
                    except Exception as e:
                        logger.error(f"Failed to add column '{col_name}' to table 'ai_insights': {str(e)}")

