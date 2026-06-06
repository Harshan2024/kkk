"""
safe_db.py — CarbonTracker Safe Database Utility
=================================================
LOCKED: Core infrastructure utility. Do not modify without team review.

Provides safe database operation wrappers with retry loops, exponential backoff,
and Read-Only Degraded Mode enforcement on connection exhaustion.
"""
import time
import logging
from contextlib import contextmanager
from typing import TypeVar, Callable, Any, Optional
from sqlalchemy.orm import Session
from app.utils.logger import log_structured, request_id_var
from app.utils.metrics import obs_metrics

T = TypeVar("T")

class DatabaseUnavailableException(Exception):
    """Raised when the database is unreachable and read-only degraded mode is active."""
    def __init__(self, message: str = "Database temporarily unavailable. Read-only mode active."):
        self.message = message
        super().__init__(message)


def run_db_with_retry(
    operation: Callable[[], T],
    operation_name: str = "db_operation",
    fallback: T = None,
    db: Optional[Session] = None
) -> T:
    """
    Executes a database query/action with up to 3 retries (4 attempts total)
    using exponential backoff (0.5s, 1s, 2s).
    If database is in READ_ONLY_MODE:
      - Instantly raises DatabaseUnavailableException for write operations.
      - Executes read operations exactly once without retry delays.
    If all attempts fail, activates READ_ONLY_MODE, logs a critical error, and returns fallback.
    """
    # Import READ_ONLY_MODE dynamically to avoid circular references
    from app.database import session as db_session

    is_write = operation_name in ("commit", "log_activity", "save_chat_message", "record_user_correction", "create_user", "delete_insights", "seed")

    if db_session.READ_ONLY_MODE and is_write:
        raise DatabaseUnavailableException("Database temporarily unavailable. Read-only mode active.")

    retries = 3
    base_delay = 0.5
    
    # If read-only mode is active, reads should not retry (fails fast to prevent UI blocking)
    max_attempts = 1 if (db_session.READ_ONLY_MODE and not is_write) else (retries + 1)

    for attempt in range(1, max_attempts + 1):
        try:
            return operation()
        except Exception as e:
            delay = base_delay * (2 ** (attempt - 1))
            
            log_structured(
                level="WARNING",
                service="safe_db",
                message=f"Database operation '{operation_name}' attempt {attempt}/{max_attempts} failed. "
                        f"Retrying in {delay if attempt < max_attempts else 0}s... Error: {e}",
                context={"operation_name": operation_name, "attempt": attempt},
                exception=e
            )
            obs_metrics.increment("db_retries")
            
            if db:
                try:
                    db.rollback()
                except Exception as rb_err:
                    log_structured(
                        level="ERROR",
                        service="safe_db",
                        message=f"Rollback failed during retry rollback of '{operation_name}': {rb_err}",
                        exception=rb_err
                    )
            
            if attempt < max_attempts:
                time.sleep(delay)
            else:
                # All retries failed
                log_structured(
                    level="CRITICAL",
                    service="safe_db",
                    message=f"All retries failed for database operation '{operation_name}'. Activating Read-Only Degraded Mode.",
                    context={"operation_name": operation_name},
                    exception=e
                )
                
                # Activate read-only degraded mode
                if not db_session.READ_ONLY_MODE:
                    db_session.READ_ONLY_MODE = True
                    obs_metrics.increment("recovery_mode_activations")
                
                if is_write:
                    raise DatabaseUnavailableException("Database temporarily unavailable. Read-only mode active.")
                
                return fallback


@contextmanager
def safe_db_op(db: Session, operation_name: str = "db_operation", fallback=None):
    """
    Context manager that wraps database operations safely.
    Note: Inline block execution inside 'with' cannot be retried automatically.
    """
    class _Guard:
        ok = True
        result = fallback

    guard = _Guard()
    from app.database import session as db_session
    if db_session.READ_ONLY_MODE:
        guard.ok = False
        yield guard
        return

    try:
        yield guard
    except Exception as e:
        guard.ok = False
        guard.result = fallback
        try:
            db.rollback()
        except Exception as rb_err:
            log_structured(
                level="ERROR",
                service="safe_db",
                message=f"Rollback also failed during '{operation_name}': {rb_err}",
                exception=rb_err
            )
        log_structured(
            level="ERROR",
            service="safe_db",
            message=f"Operation '{operation_name}' failed: {type(e).__name__}: {e}",
            context={"operation_name": operation_name},
            exception=e
        )


def safe_commit(db: Session, operation_name: str = "commit") -> bool:
    """
    Safely commits a database session with retry logic.
    Returns True on success, raises DatabaseUnavailableException if in Read-Only mode or if retries fail.
    """
    def _action():
        db.commit()
        return True
    
    try:
        return run_db_with_retry(_action, operation_name=operation_name, fallback=False, db=db)
    except DatabaseUnavailableException:
        raise
    except Exception:
        return False


def safe_scalar(query, default: Any = None) -> Any:
    """
    Safely executes a SQLAlchemy scalar query with retry logic.
    """
    return run_db_with_retry(query.scalar, operation_name="scalar", fallback=default)


def safe_query_all(query, default=None):
    """
    Safely executes a SQLAlchemy .all() query with retry logic.
    """
    if default is None:
        default = []
    return run_db_with_retry(query.all, operation_name="query_all", fallback=default)


def safe_query_first(query, default=None):
    """
    Safely executes a SQLAlchemy .first() query with retry logic.
    """
    return run_db_with_retry(query.first, operation_name="query_first", fallback=default)


def safe_count(query, default: int = 0) -> int:
    """
    Safely executes a count() query with retry logic.
    """
    return run_db_with_retry(query.count, operation_name="count", fallback=default)
