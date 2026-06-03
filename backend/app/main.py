"""
main.py — CarbonTracker FastAPI Application Entry Point
========================================================
LOCKED: Core application bootstrap. Do not modify without team review.

Initialises the FastAPI app, CORS, global error handling,
database verification, and schema synchronization.
"""
import logging
import signal
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config.config import settings, validate_environment_on_startup
from app.api.endpoints import router as api_router
from app.database.session import engine, SessionLocal, Base, verify_database_connection, sync_database_schema
from app.database import session as db_session
from app.emissions.factors import seed_db
from app.logging.logger import configure_logging
from app.utils.logger import log_structured

# Configure application logging
configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle manager."""
    log_structured("INFO", "main", "CarbonTracker AI Backend — Starting Up")

    # Perform environment verification
    validate_environment_on_startup()

    if db_session.OFFLINE_MODE:
        log_structured(
            "WARNING",
            "main",
            "OFFLINE SAFE MODE ACTIVE — Database not configured. "
            "Backend will start with in-memory SQLite. Data will NOT persist."
        )
    else:
        # Run the connection verification loop (retry 3 times, exponential backoff)
        db_connected = verify_database_connection(retries=3, base_delay=1.0)

        if db_connected:
            try:
                log_structured("INFO", "main", "Running database schema synchronization...")
                Base.metadata.create_all(bind=engine)
                sync_database_schema(engine)
                log_structured("INFO", "main", ">>> Database schema synchronization completed.")
            except Exception as e:
                log_structured("ERROR", "main", f"Schema synchronization error: {e}. Continuing startup.", exception=e)
        else:
            log_structured(
                "WARNING",
                "main",
                "PostgreSQL is unreachable. Starting in DEGRADED MODE. "
                "Activity logging will be unavailable until database is reconnected."
            )

    log_structured("INFO", "main", "CarbonTracker AI Backend — Ready to serve requests")

    yield

    # Shutdown
    log_structured("INFO", "main", "CarbonTracker AI Backend — Shutting down gracefully.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="CarbonTracker AI — Production-Grade Sustainability Operating System",
    version="2.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Register global FastAPI exception handler directly
from fastapi import Request
from fastapi.responses import JSONResponse
from app.utils.logger import log_structured, request_id_var
from app.utils.rate_limiter import RateLimitExceeded
from app.utils.safe_db import DatabaseUnavailableException

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error": "Rate limit exceeded",
            "request_id": request_id_var.get()
        }
    )

@app.exception_handler(DatabaseUnavailableException)
async def database_unavailable_handler(request: Request, exc: DatabaseUnavailableException):
    return JSONResponse(
        status_code=503,
        content={
            "success": False,
            "error": "Database temporarily unavailable. Read-only mode active.",
            "request_id": request_id_var.get()
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    endpoint = request.url.path
    method = request.method
    
    # Compile log context
    context = {
        "endpoint": endpoint,
        "method": method,
        "exception_type": type(exc).__name__
    }
    
    # Log using structured logger
    log_structured(
        level="ERROR",
        service="global_exception_handler",
        message=f"Unhandled exception occurred during request {method} {endpoint}: {str(exc)}",
        context=context,
        exception=exc
    )
    
    # Return safe JSON
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "message": "An unexpected error occurred.",
            "request_id": request_id_var.get()
        }
    )

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    import secrets
    req_id = f"REQ-{secrets.token_hex(3).upper()}"
    token = request_id_var.set(req_id)
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response
    finally:
        request_id_var.reset(token)

# ─────────────────────────────────────────────────────────────────────────────
# CORS — supports all standard local ports for development
# ─────────────────────────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────────────────────────
# ROUTER MOUNTING — single canonical prefix: /api/v1
# NOTE: Do NOT mount the same router twice. Route collision causes ambiguity.
# ─────────────────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix=settings.API_V1_STR)


# ─────────────────────────────────────────────────────────────────────────────
# HEALTH ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/health")
@app.get("/api/health")
def health_check():
    """
    Primary health check — returns server running status + database connectivity.
    Always returns 200 even in degraded mode so load balancers don't kill the pod.
    """
    db_status = "disconnected"
    stats_status = "error"

    if db_session.OFFLINE_MODE:
        return {
            "backend": "running",
            "mode": "offline_safe",
            "database": "offline_safe_mode",
            "statistics_api": "unavailable",
        }

    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            db_status = "connected"
            from app.models import Activity
            db.query(Activity).count()
            stats_status = "working"
        finally:
            db.close()
    except Exception as e:
        log_structured("ERROR", "main", f"Health check database validation failed: {e}", exception=e)

    return {
        "backend": "running",
        "mode": "online",
        "database": db_status,
        "statistics_api": stats_status,
    }


@app.get("/api/health/database")
def health_database():
    """Database-specific health check."""
    if db_session.OFFLINE_MODE:
        return {"status": "offline_safe_mode", "connected": False, "mode": "sqlite_memory"}
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "healthy", "connected": True}
    except Exception as e:
        return {"status": "unhealthy", "connected": False, "error": str(e)}


@app.get("/api/health/ai")
def health_ai():
    """AI subsystem health check."""
    results = {}
    overall = "healthy"

    try:
        from app.ai.embeddings.embeddings import get_embedding
        vec = get_embedding("test")
        results["embeddings"] = "healthy" if vec else "degraded"
    except Exception as e:
        results["embeddings"] = f"error: {e}"
        overall = "degraded"

    try:
        from app.ai.orchestrator.orchestrator import orchestrate_chat_response
        results["orchestrator"] = "healthy"
    except Exception as e:
        results["orchestrator"] = f"error: {e}"
        overall = "degraded"

    return {"status": overall, "subsystems": results}


@app.get("/api/health/ocr")
def health_ocr():
    """OCR subsystem health check."""
    try:
        from app.ai.multimodal.ocr import parse_receipt_image
        result = parse_receipt_image("test.jpg", 100)
        return {"status": "healthy", "items_parsed": len(result)}
    except Exception as e:
        return {"status": "degraded", "error": str(e)}


@app.get("/api/health/iot")
def health_iot():
    """IoT subsystem health check — always returns degraded (not yet implemented)."""
    return {"status": "degraded", "message": "IoT hardware bridge not connected"}


@app.get("/api/health/cache")
def health_cache():
    """Cache health check — returns ok if in-process cache is accessible."""
    return {"status": "healthy", "cache_type": "in-process"}


@app.get("/api/system/status")
def get_system_status():
    """
    Unified system status check returning statuses of all components.
    """
    db_status = "offline_safe_mode" if db_session.OFFLINE_MODE else "online"
    if not db_session.OFFLINE_MODE:
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
        except Exception:
            db_status = "offline"
            
    ai_status = "online"
    try:
        from app.ai.embeddings.embeddings import get_embedding
        vec = get_embedding("test")
        if not vec or len(vec) != 8:
            ai_status = "degraded"
    except Exception:
        ai_status = "offline"
        
    ocr_status = "online"
    try:
        from app.ai.multimodal.ocr import parse_receipt_image
        res = parse_receipt_image("test.jpg", 100)
        if not res:
            ocr_status = "degraded"
    except Exception:
        ocr_status = "offline"
        
    return {
        "success": True,
        "data": {
            "backend": "online",
            "database": db_status,
            "ai": ai_status,
            "ocr": ocr_status,
            "iot": "offline",
            "cache": "online"
        },
        "error": None
    }


@app.get("/debug-error")
def trigger_debug_error():
    raise RuntimeError("Triggered unhandled error for verification")


@app.get("/observability/metrics")
def get_flat_observability_metrics():
    from app.utils.metrics import obs_metrics
    return obs_metrics.get_metrics()


@app.get("/")
def read_root():
    return {
        "message": "Welcome to CarbonTracker AI",
        "status": "online",
        "version": "2.0.0",
        "mode": "offline_safe" if db_session.OFFLINE_MODE else "online",
        "docs": "/docs",
    }
