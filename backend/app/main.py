"""
main.py — CarbonTracker FastAPI Application Entry Point
========================================================
LOCKED: Core application bootstrap. Do not modify without team review.

Initialises the FastAPI app, CORS, global error handling,
database verification, and schema synchronization.
"""
import os
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


import time
import threading

def initialize_database_background():
    """Verifies database connection and runs schema synchronization in a background thread."""
    t_db = time.perf_counter()
    print("Connecting Database (background)")
    log_structured("INFO", "main", "Connecting Database (background)")
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
    db_time = (time.perf_counter() - t_db) * 1000
    print(f"Connecting Database completed in {db_time:.2f}ms (background)")
    log_structured("INFO", "main", f"Connecting Database completed in {db_time:.2f}ms (background)")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle manager."""
    t_start = time.perf_counter()
    print("Backend Starting")
    log_structured("INFO", "main", "Backend Starting")

    # Loading Configuration
    t_config = time.perf_counter()
    print("Loading Configuration")
    log_structured("INFO", "main", "Loading Configuration")
    validate_environment_on_startup()
    config_time = (time.perf_counter() - t_config) * 1000
    print(f"Loading Configuration completed in {config_time:.2f}ms")
    log_structured("INFO", "main", f"Loading Configuration completed in {config_time:.2f}ms")

    # Connecting Database in Background
    threading.Thread(target=initialize_database_background, daemon=True).start()

    # Pre-warm spaCy NLP model in background to prevent first-query lag/freeze
    def pre_warm_nlp():
        try:
            from app.nlp.parser import get_nlp
            print("Pre-warming spaCy NLP model in background...")
            get_nlp()
            print("spaCy NLP model pre-warming completed.")
        except Exception as e:
            print(f"Failed to pre-warm spaCy: {e}")

    threading.Thread(target=pre_warm_nlp, daemon=True).start()

    # Registering Routes
    t_routes = time.perf_counter()
    print("Registering Routes")
    log_structured("INFO", "main", "Registering Routes")
    # Routes are registered automatically as the module is imported; we confirm here
    routes_time = (time.perf_counter() - t_routes) * 1000
    print(f"Registering Routes completed in {routes_time:.2f}ms")
    log_structured("INFO", "main", f"Registering Routes completed in {routes_time:.2f}ms")

    total_time = (time.perf_counter() - t_start) * 1000
    print("Backend Ready")
    print(f"Total backend startup completed in {total_time:.2f}ms")
    log_structured("INFO", "main", "Backend Ready")

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

@app.middleware("http")
async def request_timing_middleware(request: Request, call_next):
    import time
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = (time.perf_counter() - start_time) * 1000
    
    log_msg = f"{request.method} {request.url.path} {int(process_time)}ms"
    print(log_msg)
    # For production logs clarity, only log structure on warnings/errors, print locally
    # log_structured("INFO", "middleware", log_msg, context={
    #     "method": request.method,
    #     "endpoint": request.url.path,
    #     "execution_time_ms": round(process_time, 2)
    # })
    return response

# ─────────────────────────────────────────────────────────────────────────────
# CORS — supports all standard local ports for development
# ─────────────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # localhost variants
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        # 127.0.0.1 variants (browser treats these differently from localhost)
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:3003",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# ─────────────────────────────────────────────────────────────────────────────
# ROUTER MOUNTING — single canonical prefix: /api/v1
# NOTE: Do NOT mount the same router twice. Route collision causes ambiguity.
# ─────────────────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix=settings.API_V1_STR)


# ─────────────────────────────────────────────────────────────────────────────
# HEALTH ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────
from datetime import datetime

# For testing and verification suite overrides
MOCK_STATUS_OVERRIDES = {}

@app.get("/health")
def health_check():
    """
    Lightweight health check returning status and backend online.
    No database queries.
    """
    return {
        "status": "ok",
        "backend": "online"
    }


@app.get("/api/health")
def api_health_check():
    """
    Detailed API health check for compatibility.
    """
    from app.utils.cache import global_cache
    db_ok = True
    if not db_session.OFFLINE_MODE:
        from app.database.session import check_database_health_throttled
        db_ok = check_database_health_throttled()
        if db_ok:
            if db_session.READ_ONLY_MODE:
                db_session.READ_ONLY_MODE = False
                log_structured("INFO", "main", "Database connection recovered via api_health_check! Clearing READ_ONLY_MODE.")
        else:
            db_session.READ_ONLY_MODE = True
            
    cache_ok = global_cache.validate() == "healthy"
    
    status_val = "healthy"
    if not db_ok or not cache_ok:
        status_val = "degraded"
        
    return {
        "status": status_val,
        "service": "backend",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/api/health/database")
def health_database():
    """Database-specific health check."""
    if db_session.OFFLINE_MODE:
        return {"status": "offline_safe_mode", "connected": False, "mode": "sqlite_memory"}
    
    from app.database.session import check_database_health_throttled
    is_healthy = check_database_health_throttled()
    if is_healthy:
        if db_session.READ_ONLY_MODE:
            db_session.READ_ONLY_MODE = False
            log_structured("INFO", "main", "Database connection recovered via health_database! Clearing READ_ONLY_MODE.")
        return {"status": "healthy", "connected": True}
    else:
        db_session.READ_ONLY_MODE = True
        return {"status": "unhealthy", "connected": False}


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
    if "cache" in MOCK_STATUS_OVERRIDES:
        # Map 'online' or other override states to healthy/degraded format
        val = MOCK_STATUS_OVERRIDES["cache"]
        if val == "online":
            return {"cache": "healthy"}
        return {"cache": val}
    from app.utils.cache import global_cache
    status = global_cache.validate()
    return {"cache": status}


@app.get("/api/system/status")
def get_system_status():
    """
    Unified system status check returning statuses of all components.
    Lightweight version.
    """
    t_start = time.perf_counter()
    backend_status = MOCK_STATUS_OVERRIDES.get("backend", "online")
    
    # Check database status dynamically but in a lightweight way
    if "database" in MOCK_STATUS_OVERRIDES:
        db_status = MOCK_STATUS_OVERRIDES["database"]
    else:
        if db_session.OFFLINE_MODE:
            db_status = "degraded"
        else:
            from app.database.session import check_database_health_throttled
            is_healthy = check_database_health_throttled()
            if is_healthy:
                if db_session.READ_ONLY_MODE:
                    db_session.READ_ONLY_MODE = False
                    log_structured("INFO", "main", "Database connection recovered! Clearing READ_ONLY_MODE.")
                db_status = "online"
            else:
                db_session.READ_ONLY_MODE = True
                db_status = "degraded"

    elapsed_ms = (time.perf_counter() - t_start) * 1000.0
    print(f"DEBUG: get_system_status internal duration: {elapsed_ms:.4f}ms")
    return {
        "backend": backend_status,
        "database": db_status,
        "version": "current"
    }


@app.get("/debug-error")
def trigger_debug_error():
    raise RuntimeError("Triggered unhandled error for verification")


from fastapi import Depends, Request as FastAPIRequest
from sqlalchemy.orm import Session as SqlSession
from app.database.session import get_db
from app.api.endpoints import ChatRequest, post_chat_query

@app.post("/api/chat")
def api_post_chat(payload: ChatRequest, request: FastAPIRequest, db: SqlSession = Depends(get_db)):
    return post_chat_query(payload, request, db)



@app.post("/api/test/mock-status")
def set_mock_status(overrides: dict):
    """Used by verification suite to simulate subsystem failures."""
    global MOCK_STATUS_OVERRIDES
    MOCK_STATUS_OVERRIDES.clear()
    MOCK_STATUS_OVERRIDES.update(overrides)
    return {"success": True, "overrides": MOCK_STATUS_OVERRIDES}


@app.post("/api/test/trigger-failure")
def trigger_mock_failure(service: str):
    """Triggers a failure call under the specified circuit breaker to increment metrics."""
    from app.utils.circuit_breaker import breakers
    if service in breakers:
        breaker = breakers[service]
        def failing_func():
            raise RuntimeError(f"Simulated failure for {service}")
        try:
            breaker.call(failing_func)
        except Exception:
            pass
        return {"success": True, "service": service, "state": breaker.state}
    return {"success": False, "error": "Invalid service"}


@app.get("/observability/metrics")
def get_flat_observability_metrics():
    from fastapi import HTTPException
    raise HTTPException(
        status_code=503,
        detail="Observability metrics endpoint temporarily disabled during stabilization sprint."
    )


@app.get("/")
def read_root():
    return {
        "message": "Welcome to CarbonTracker AI",
        "status": "online",
        "version": "2.0.0",
        "mode": "offline_safe" if db_session.OFFLINE_MODE else "online",
        "docs": "/docs",
    }
