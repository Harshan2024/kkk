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
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool
from app.config.config import settings
from app.utils.logger import log_structured

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("carbontracker.database")

def register_engine_events(bind_engine):
    @event.listens_for(bind_engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        context._query_start_time = time.perf_counter()

    @event.listens_for(bind_engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        if hasattr(context, "_query_start_time"):
            total_time = (time.perf_counter() - context._query_start_time) * 1000
            if total_time > 500:
                log_structured("WARNING", "database_query", f"Query exceeded 500ms: {statement} took {total_time:.2f}ms")
                print(f"[WARNING] Database query exceeded 500ms: {total_time:.2f}ms for: {statement[:200]}")

# ─────────────────────────────────────────────────────────────────────────────
# OFFLINE SAFE MODE
# If DATABASE_URL is missing, use an in-memory SQLite instance so the server
# can start and serve degraded (offline-mode) responses instead of crashing.
# ─────────────────────────────────────────────────────────────────────────────
OFFLINE_MODE = False
READ_ONLY_MODE = False

if not settings.DATABASE_URL:
    log_structured(
        level="CRITICAL",
        service="database_session",
        message=(
            "DATABASE_URL is not configured. Entering READ-ONLY DEGRADED MODE. "
            "All database writes will be disabled."
        )
    )
    OFFLINE_MODE = True
    READ_ONLY_MODE = True
    _DB_URL = "sqlite://"  # In-memory SQLite — ephemeral but allows startup
    engine = create_engine(
        _DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    register_engine_events(engine)
else:
    try:
        # Create SQLAlchemy engine with resilient connection pooling
        engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=5,
            pool_recycle=300,
            pool_timeout=3,
            connect_args={"connect_timeout": 3},
        )
        register_engine_events(engine)
    except Exception as e:
        log_structured(
            level="CRITICAL",
            service="database_session",
            message=f"Failed to create SQLAlchemy engine: {e}. Entering READ-ONLY DEGRADED MODE.",
            exception=e
        )
        OFFLINE_MODE = True
        READ_ONLY_MODE = True
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        register_engine_events(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def enter_offline_mode():
    """Enters read-only degraded mode without SQLite writes."""
    global READ_ONLY_MODE, LAST_DB_CHECK_RESULT
    log_structured(
        level="CRITICAL",
        service="database_session",
        message=(
            "!!! Database connection verification failed after all retries. "
            "Entering READ-ONLY DEGRADED MODE."
        )
    )
    if not READ_ONLY_MODE:
        READ_ONLY_MODE = True
        try:
            from app.utils.metrics import obs_metrics
            obs_metrics.increment("recovery_mode_activations")
        except Exception:
            pass
    else:
        READ_ONLY_MODE = True
    LAST_DB_CHECK_RESULT = False
    # Try to seed default factors in the fallback DB just in case, but keep writes disabled
    try:
        from app.emissions.factors import seed_db
        db = SessionLocal()
        seed_db(db)
        db.close()
        log_structured("INFO", "database_session", "Successfully seeded default factors in fallback SQLite DB.")
    except Exception as se:
        log_structured("ERROR", "database_session", f"Failed to seed fallback database: {se}", exception=se)

def verify_database_connection(retries: int = 3, base_delay: float = 0.5) -> bool:
    """
    Attempts to connect to the database with a retry loop.
    Retries 3 times with exponential backoff (e.g. 0.5s, 1s, 2s).
    Returns True if connection is verified, False otherwise.
    Never raises — always returns bool.
    """
    global READ_ONLY_MODE, LAST_DB_CHECK_RESULT
    if OFFLINE_MODE and READ_ONLY_MODE:
        log_structured("WARNING", "database_session", "Database is in READ-ONLY DEGRADED MODE — skipping connection verification.")
        return False

    log_structured("INFO", "database_session", f"Verifying PostgreSQL database connection (Retries: {retries})...")
    start_time = time.perf_counter()
    for attempt in range(1, retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            elapsed_time = (time.perf_counter() - start_time) * 1000
            print(f"Database Connection Time: {elapsed_time:.2f}ms")
            log_structured("INFO", "database_session", f"Database Connection Time: {elapsed_time:.2f}ms")
            LAST_DB_CHECK_RESULT = True
            return True
        except Exception as e:
            delay = base_delay * (2 ** (attempt - 1))
            log_structured(
                level="WARNING",
                service="database_session",
                message=f"Database connection attempt {attempt}/{retries} failed. Retrying in {delay:.1f}s... Error: {e}",
                exception=e
            )
            from app.utils.metrics import obs_metrics
            obs_metrics.increment("db_retries")
            if attempt < retries:
                time.sleep(delay)

    # All retries failed — enter read-only degraded mode
    elapsed_time = (time.perf_counter() - start_time) * 1000
    print(f"Database Connection Time: {elapsed_time:.2f}ms (failed)")
    log_structured("INFO", "database_session", f"Database Connection Time: {elapsed_time:.2f}ms (failed)")
    enter_offline_mode()
    return False


# Throttled health check states
LAST_DB_CHECK_TIME = 0.0
DB_CHECK_THROTTLE_SECONDS = 5.0
LAST_DB_CHECK_RESULT = False

def check_database_health_fast() -> bool:
    """
    Performs a fast, single-attempt check by checking out a connection from the pool.
    With pool_pre_ping=True, checking out a connection automatically executes a ping query.
    Returns True if database is reachable, False otherwise.
    """
    if OFFLINE_MODE:
        return False
    try:
        with engine.connect() as conn:
            pass
        return True
    except Exception:
        return False

def check_database_health_throttled() -> bool:
    """
    Performs a database health check, throttled to prevent spamming
    and blocking the server when the database is down.
    Uses a background thread to perform the actual check so it never blocks the request thread.
    """
    global LAST_DB_CHECK_TIME, LAST_DB_CHECK_RESULT
    if OFFLINE_MODE:
        return False
        
    now = time.time()
    if now - LAST_DB_CHECK_TIME >= DB_CHECK_THROTTLE_SECONDS:
        LAST_DB_CHECK_TIME = now
        def run_health_check_bg():
            global LAST_DB_CHECK_RESULT
            try:
                LAST_DB_CHECK_RESULT = check_database_health_fast()
            except Exception:
                LAST_DB_CHECK_RESULT = False
        import threading
        threading.Thread(target=run_health_check_bg, daemon=True).start()
        
    return LAST_DB_CHECK_RESULT



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
            log_structured("ERROR", "database_session", f"Failed to close database session: {e}", exception=e)


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
        log_structured("ERROR", "database_session", f"Schema sync: Failed to create inspector: {e}", exception=e)
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
                        log_structured("INFO", "database_session", f"Adding missing column '{col_name}' to 'chat_messages'...")
                        try:
                            conn.execute(sql_text(f"ALTER TABLE chat_messages ADD COLUMN {col_name} {col_def}"))
                            conn.commit()
                        except Exception as e:
                            log_structured("ERROR", "database_session", f"Failed to add '{col_name}' to chat_messages: {e}", exception=e)

                # context_tags — try JSON first, fallback to TEXT
                if "context_tags" not in columns:
                    log_structured("INFO", "database_session", "Adding missing column 'context_tags' to 'chat_messages'...")
                    try:
                        conn.execute(sql_text("ALTER TABLE chat_messages ADD COLUMN context_tags JSON NULL"))
                        conn.commit()
                    except Exception:
                        try:
                            conn.execute(sql_text("ALTER TABLE chat_messages ADD COLUMN context_tags TEXT NULL"))
                            conn.commit()
                        except Exception as e2:
                            log_structured("ERROR", "database_session", f"Failed to add context_tags (fallback): {e2}", exception=e2)
    except Exception as e:
        log_structured("ERROR", "database_session", f"Schema sync failed for chat_messages: {e}", exception=e)

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
                        log_structured("INFO", "database_session", f"Adding missing column '{col_name}' to 'ai_insights'...")
                        try:
                            conn.execute(sql_text(f"ALTER TABLE ai_insights ADD COLUMN {col_name} {col_sql}"))
                            conn.commit()
                        except Exception as e:
                            log_structured("ERROR", "database_session", f"Failed to add '{col_name}' to ai_insights: {e}", exception=e)
    except Exception as e:
        log_structured("ERROR", "database_session", f"Schema sync failed for ai_insights: {e}", exception=e)

    # 3. Check table "users"
    try:
        if "users" in inspector.get_table_names():
            columns = [col["name"] for col in inspector.get_columns("users")]
            with bind_engine.connect() as conn:
                for col_name, col_def in [
                    ("email", "VARCHAR(255) NULL UNIQUE"),
                    ("hashed_password", "VARCHAR(255) NULL"),
                    ("is_active", "BOOLEAN NOT NULL DEFAULT TRUE"),
                    ("is_verified", "BOOLEAN NOT NULL DEFAULT FALSE"),
                    ("role", "VARCHAR(50) NOT NULL DEFAULT 'user'"),
                    ("last_login", "TIMESTAMP WITHOUT TIME ZONE NULL"),
                ]:
                    if col_name not in columns:
                        log_structured("INFO", "database_session", f"Adding missing column '{col_name}' to 'users'...")
                        try:
                            conn.execute(sql_text(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}"))
                            conn.commit()
                        except Exception as e:
                            log_structured("ERROR", "database_session", f"Failed to add '{col_name}' to users: {e}", exception=e)
    except Exception as e:
        log_structured("ERROR", "database_session", f"Schema sync failed for users: {e}", exception=e)
