"""
safe_db.py — CarbonTracker Safe Database Utility
=================================================
LOCKED: Core infrastructure utility. Do not modify without team review.

Provides a safe_query() context manager that wraps any SQLAlchemy
database operation with automatic rollback on failure, preventing
any single DB failure from crashing the caller.
"""
import logging
import functools
from contextlib import contextmanager
from typing import TypeVar, Callable, Any, Optional
from sqlalchemy.orm import Session

logger = logging.getLogger("carbontracker.safe_db")

T = TypeVar("T")


@contextmanager
def safe_db_op(db: Session, operation_name: str = "db_operation", fallback=None):
    """
    Context manager that wraps a database operation safely.

    Usage:
        with safe_db_op(db, "update_score", fallback=None) as guard:
            if guard.ok:
                db.add(record)
                db.commit()

    On exception:
        - Rolls back the session
        - Logs the error with full context
        - Returns fallback value instead of raising
    """
    class _Guard:
        ok = True
        result = fallback

    guard = _Guard()
    try:
        yield guard
    except Exception as e:
        guard.ok = False
        guard.result = fallback
        try:
            db.rollback()
        except Exception as rb_err:
            logger.error(f"[safe_db] Rollback also failed during '{operation_name}': {rb_err}")
        logger.error(
            f"[safe_db] Operation '{operation_name}' failed: {type(e).__name__}: {e}",
            exc_info=True
        )


def safe_commit(db: Session, operation_name: str = "commit") -> bool:
    """
    Safely commits a database session.
    Returns True on success, False on failure (with automatic rollback).
    """
    try:
        db.commit()
        return True
    except Exception as e:
        logger.error(f"[safe_db] Commit failed during '{operation_name}': {type(e).__name__}: {e}")
        try:
            db.rollback()
        except Exception as rb_err:
            logger.error(f"[safe_db] Rollback also failed: {rb_err}")
        return False


def safe_scalar(query, default: Any = None) -> Any:
    """
    Safely executes a SQLAlchemy scalar query.
    Returns default value instead of raising on failure.
    """
    try:
        result = query.scalar()
        return result if result is not None else default
    except Exception as e:
        logger.error(f"[safe_db] Scalar query failed: {type(e).__name__}: {e}")
        return default


def safe_query_all(query, default=None):
    """
    Safely executes a SQLAlchemy .all() query.
    Returns empty list or default on failure.
    """
    if default is None:
        default = []
    try:
        return query.all()
    except Exception as e:
        logger.error(f"[safe_db] Query .all() failed: {type(e).__name__}: {e}")
        return default


def safe_query_first(query, default=None):
    """
    Safely executes a SQLAlchemy .first() query.
    Returns default on failure.
    """
    try:
        return query.first()
    except Exception as e:
        logger.error(f"[safe_db] Query .first() failed: {type(e).__name__}: {e}")
        return default


def safe_count(query, default: int = 0) -> int:
    """
    Safely executes a count() query.
    """
    try:
        return query.count()
    except Exception as e:
        logger.error(f"[safe_db] Count query failed: {type(e).__name__}: {e}")
        return default
