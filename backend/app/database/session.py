"""
session.py — CarbonTracker Database Session
============================================
LOCKED: Core infrastructure. Do not modify without team review.

Provides SQLAlchemy engine, session factory, and startup verification.
Includes offline-safe mode: if DATABASE_URL is missing or unreachable,
the backend enters a degraded-but-running state instead of crashing.
"""
import time
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool
from app.config.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("carbontracker.database")

# ─────────────────────────────────────────────────────────────────────────────
# OFFLINE SAFE MODE
# If DATABASE_URL is missing, use an in-memory SQLite instance so the server
# can start and serve degraded (offline-mode) responses instead of crashing.
# ─────────────────────────────────────────────────────────────────────────────
OFFLINE_MODE = False

if not settings.DATABASE_URL:
    logger.critical(
        "DATABASE_URL is not configured. Entering OFFLINE SAFE MODE. "
        "All database operations will use an in-memory SQLite instance. "
        "Data will not be persisted. Set DATABASE_URL in backend/.env to restore."
    )
    OFFLINE_MODE = True
    _DB_URL = "sqlite://"  # In-memory SQLite — ephemeral but allows startup
    engine = create_engine(
        _DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    try:
        # Create SQLAlchemy engine with resilient connection pooling
        # pool_recycle: Recycles connections older than 5 minutes (prevents serverless dropouts)
        # pool_pre_ping: Checks if connection is alive before serving a query
        # pool_timeout: Limits thread waiting to 15 seconds
        engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            pool_size=15,
            max_overflow=25,
            pool_recycle=300,
            pool_timeout=15,
        )
    except Exception as e:
        logger.critical(
            f"Failed to create SQLAlchemy engine: {e}. "
            "Entering OFFLINE SAFE MODE with in-memory SQLite."
        )
        OFFLINE_MODE = True
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def enter_offline_mode():
    """Reconfigures the DB sessionmaker to use SQLite in offline safe mode."""
    global engine, SessionLocal, OFFLINE_MODE
    logger.critical(
        "!!! Database connection verification failed after all retries. "
        "Entering OFFLINE SAFE MODE with in-memory SQLite."
    )
    OFFLINE_MODE = True
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal.configure(bind=engine)
    # Create schemas in the fresh in-memory DB
    Base.metadata.create_all(bind=engine)
    
    # Try to seed default factors in the fallback DB
    try:
        from app.emissions.factors import seed_db
        db = SessionLocal()
        seed_db(db)
        db.close()
        logger.info("Successfully seeded default factors in fallback SQLite DB.")
    except Exception as se:
        logger.error(f"Failed to seed fallback database: {se}")

def verify_database_connection(retries: int = 3, base_delay: float = 1.0) -> bool:
    """
    Attempts to connect to the database with a retry loop.
    Retries 3 times with exponential backoff (e.g. 1s, 2s, 4s).
    Returns True if connection is verified, False otherwise.
    Never raises — always returns bool.
    """
    if OFFLINE_MODE:
        logger.warning("Database is in OFFLINE SAFE MODE — skipping connection verification.")
        return False

    logger.info(f"Verifying PostgreSQL database connection (Retries: {retries})...")
    for attempt in range(1, retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                conn.commit()
            logger.info(">>> PostgreSQL Database connection verified successfully.")
            return True
        except Exception as e:
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning(
                f"Database connection attempt {attempt}/{retries} failed. "
                f"Retrying in {delay:.1f}s... Error: {e}"
            )
            if attempt < retries:
                time.sleep(delay)

    # All retries failed — enter offline safe mode
    enter_offline_mode()
    return False


def get_db():
    """
    FastAPI dependency generator for database sessions.
    Yields a session and ensures it is closed after request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        try:
            db.close()
        except Exception as e:
            logger.error(f"Failed to close database session: {e}")


def sync_database_schema(bind_engine) -> None:
    """
    Verifies and adds missing columns for Phase-3 models dynamically.
    Helps sync schemas on PostgreSQL/SQLite without dropping existing table data.
    All ALTER TABLE operations are individually try/caught.
    """
    try:
        from sqlalchemy import inspect, text as sql_text
        inspector = inspect(bind_engine)
    except Exception as e:
        logger.error(f"Schema sync: Failed to create inspector: {e}")
        return

    # 1. Check table "chat_messages"
    try:
        if "chat_messages" in inspector.get_table_names():
            columns = [col["name"] for col in inspector.get_columns("chat_messages")]
            with bind_engine.connect() as conn:
                for col_name, col_def in [
                    ("embedding_id", "VARCHAR(500) NULL"),
                    ("semantic_summary", "VARCHAR(1000) NULL"),
                ]:
                    if col_name not in columns:
                        logger.info(f"Adding missing column '{col_name}' to 'chat_messages'...")
                        try:
                            conn.execute(sql_text(f"ALTER TABLE chat_messages ADD COLUMN {col_name} {col_def}"))
                            conn.commit()
                        except Exception as e:
                            logger.error(f"Failed to add '{col_name}' to chat_messages: {e}")

                # context_tags — try JSON first, fallback to TEXT
                if "context_tags" not in columns:
                    logger.info("Adding missing column 'context_tags' to 'chat_messages'...")
                    try:
                        conn.execute(sql_text("ALTER TABLE chat_messages ADD COLUMN context_tags JSON NULL"))
                        conn.commit()
                    except Exception:
                        try:
                            conn.execute(sql_text("ALTER TABLE chat_messages ADD COLUMN context_tags TEXT NULL"))
                            conn.commit()
                        except Exception as e2:
                            logger.error(f"Failed to add context_tags (fallback): {e2}")
    except Exception as e:
        logger.error(f"Schema sync failed for chat_messages: {e}")

    # 2. Check table "ai_insights"
    try:
        if "ai_insights" in inspector.get_table_names():
            columns = [col["name"] for col in inspector.get_columns("ai_insights")]
            db_driver = bind_engine.url.drivername
            is_postgres = "postgres" in db_driver or "psycopg" in db_driver
            float_type = "DOUBLE PRECISION" if is_postgres else "FLOAT"

            new_cols = {
                "impact_value": f"{float_type} NULL",
                "feasibility": "VARCHAR(50) NULL",
                "difficulty": "VARCHAR(50) NULL",
                "confidence_score": f"{float_type} NULL",
                "sustainability_gain": f"{float_type} NULL",
                "behavioral_compatibility": f"{float_type} NULL",
                "why_explanation": "VARCHAR(2000) NULL",
                "how_calculation": "VARCHAR(2000) NULL",
                "weighted_priority_score": f"{float_type} NULL",
            }
            with bind_engine.connect() as conn:
                for col_name, col_sql in new_cols.items():
                    if col_name not in columns:
                        logger.info(f"Adding missing column '{col_name}' to 'ai_insights'...")
                        try:
                            conn.execute(sql_text(f"ALTER TABLE ai_insights ADD COLUMN {col_name} {col_sql}"))
                            conn.commit()
                        except Exception as e:
                            logger.error(f"Failed to add '{col_name}' to ai_insights: {e}")
    except Exception as e:
        logger.error(f"Schema sync failed for ai_insights: {e}")
