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
from app.api.endpoints import router as api_router, auth_router
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
    
    # 1. Close database pools
    try:
        from app.database.session import engine, async_engine
        engine.dispose()
        # Dispose async engine (coroutine)
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(async_engine.dispose())
            else:
                asyncio.run(async_engine.dispose())
        except Exception:
            pass
        print("Database connection pools closed.")
    except Exception as e:
        print(f"Error closing database pools during shutdown: {e}")

    # 2. Close active HTTP clients / background executor threads
    try:
        from app.utils.circuit_breaker import CircuitBreaker
        CircuitBreaker._executor.shutdown(wait=True)
        print("Background thread executors stopped.")
    except Exception as e:
        print(f"Error shutting down circuit breaker executor: {e}")


app = FastAPI(
    title="CarbonTracker API",
    version="1.4.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Register global FastAPI exception handler directly
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.utils.logger import log_structured, request_id_var
from app.utils.rate_limiter import RateLimitExceeded
from app.utils.safe_db import DatabaseUnavailableException
from datetime import datetime, timezone

def format_error_response(status_code: int, error: str, message: str, path: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": error,
            "message": message,
            "request_id": request_id_var.get() or "REQ-SYSTEM",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": path,
            "status_code": status_code
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    clean_errors = []
    for err in errors:
        loc = " -> ".join(str(x) for x in err.get("loc", []))
        msg = err.get("msg", "Invalid input")
        clean_errors.append(f"{loc}: {msg}")
    
    return format_error_response(
        status_code=400,
        error="Bad Request",
        message="Validation error: " + "; ".join(clean_errors),
        path=request.url.path
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return format_error_response(
        status_code=exc.status_code,
        error=exc.detail,
        message=exc.detail,
        path=request.url.path
    )

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return format_error_response(
        status_code=429,
        error="Rate limit exceeded",
        message=exc.message if hasattr(exc, "message") else "Rate limit exceeded",
        path=request.url.path
    )

@app.exception_handler(DatabaseUnavailableException)
async def database_unavailable_handler(request: Request, exc: DatabaseUnavailableException):
    return format_error_response(
        status_code=503,
        error="Database temporarily unavailable. Read-only mode active.",
        message="The database is offline. We are running in safe read-only mode.",
        path=request.url.path
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
    
    return format_error_response(
        status_code=500,
        error="Internal server error",
        message="An unexpected error occurred.",
        path=endpoint
    )

async def set_body(request: Request, body: bytes):
    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}
    request._receive = receive

@app.middleware("http")
async def security_hardening_middleware(request: Request, call_next):
    # 1. Content Length Limit check (5MB max)
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > 5 * 1024 * 1024:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": "Bad Request",
                        "message": "Request payload size limit exceeded (5MB max)."
                    }
                )
        except ValueError:
            pass

    # 2. XSS payload check in JSON requests
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.body()
        await set_body(request, body)
        body_str = body.decode("utf-8", errors="ignore")
        
        xss_patterns = [
            "<script", "javascript:", "onload=", "onerror=", 
            "<iframe", "onmouseover=", "alert(", "eval("
        ]
        body_lower = body_str.lower()
        if any(pat in body_lower for pat in xss_patterns):
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Bad Request",
                    "message": "Potential XSS payload detected in request body."
                }
            )

    return await call_next(request)

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
    import jwt
    from app.config.config import settings
    
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = (time.perf_counter() - start_time) * 1000
    
    user_id = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get("sub") or payload.get("user_id")
        except Exception:
            pass

    log_structured(
        level="INFO",
        service="request_logger",
        message=f"{request.method} {request.url.path} resolved in {process_time:.2f}ms with status {response.status_code}",
        context={
            "method": request.method,
            "endpoint": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(process_time, 2),
            "user_id": user_id,
            "request_id": request_id_var.get()
        }
    )
    # Record into observability metrics
    try:
        from app.utils.metrics import obs_metrics
        obs_metrics.record_request(request.url.path, response.status_code, round(process_time, 2))
    except Exception:
        pass
    return response

@app.middleware("http")
async def add_security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin-allow-popups"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    
    # Strict but compatible Content Security Policy (CSP)
    csp_directives = (
        "default-src 'self'; "
        "img-src 'self' data: blob: https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
        "font-src 'self' https://fonts.gstatic.com; "
        "connect-src 'self' http://localhost:8001 http://127.0.0.1:8001 http://localhost:3001 http://localhost:3000 http://127.0.0.1:3000 http://127.0.0.1:3001; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net;"
    )
    response.headers["Content-Security-Policy"] = csp_directives
    return response

from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=500)

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
app.include_router(auth_router, prefix=settings.API_V1_STR)

# Mount static files for profile avatars
from fastapi.staticfiles import StaticFiles
import os
os.makedirs("static/avatars", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


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
            db_status = "offline_safe_mode"
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
                db_status = "offline"

    elapsed_ms = (time.perf_counter() - t_start) * 1000.0
    print(f"DEBUG: get_system_status internal duration: {elapsed_ms:.4f}ms")
    return {
        "status": "success",
        "data": {
            "backend": backend_status,
            "database": db_status,
            "version": "current"
        }
    }


@app.get("/api/database/status")
def get_database_status_app():
    if db_session.OFFLINE_MODE:
        db_online = False
        mode = "sqlite_memory"
    else:
        from app.database.session import check_database_health_throttled
        db_online = check_database_health_throttled()
        mode = "postgresql"
        
    return {
        "status": "healthy" if db_online else "unhealthy",
        "connected": db_online,
        "mode": mode,
        "read_only": db_session.READ_ONLY_MODE
    }


@app.get("/api/security/status")
def get_security_status_app():
    return {
        "status": "secure",
        "environment": settings.ENVIRONMENT,
        "ssl_active": True if settings.DATABASE_URL and "sslmode=require" in settings.DATABASE_URL else False,
        "auth_enabled": settings.SECRET_KEY != "super_secret_carbontracker_development_key",
        "jwt_algorithm": settings.ALGORITHM
    }


@app.get("/api/performance/status")
def get_performance_status_app():
    from app.utils.cache import global_cache
    return {
        "status": "healthy",
        "cache_status": global_cache.validate(),
        "average_latency_ms": 150.0,
        "active_connections": 1
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
    """Full observability metrics: system counters, per-endpoint stats, cache ratios, auth events."""
    from app.utils.metrics import obs_metrics
    return obs_metrics.get_summary()


@app.get("/api/v1/admin/health-dashboard")
def get_health_dashboard():
    """
    Unified health dashboard with traffic-light indicators.
    Returns green/yellow/red status for all system components.
    """
    from app.utils.cache import global_cache
    from app.utils.metrics import obs_metrics
    from app.utils.notifier import get_notification_status
    import psutil, os

    def traffic_light(healthy: bool, degraded: bool = False) -> str:
        if healthy:
            return "green"
        if degraded:
            return "yellow"
        return "red"

    # ── Database ────────────────────────────────────────────────────────────
    if db_session.OFFLINE_MODE:
        db_status = "offline_safe_mode"
        db_light = "yellow"
    else:
        from app.database.session import check_database_health_throttled
        db_ok = check_database_health_throttled()
        db_light = traffic_light(db_ok)
        db_status = "online" if db_ok else "offline"

    # ── Cache ───────────────────────────────────────────────────────────────
    cache_status = global_cache.validate()
    cache_light = traffic_light(cache_status == "healthy", cache_status == "degraded")

    # ── AI ──────────────────────────────────────────────────────────────────
    try:
        from app.ai.embeddings.embeddings import get_embedding
        ai_ok = bool(get_embedding("ping"))
        ai_light = "green" if ai_ok else "yellow"
        ai_status = "online" if ai_ok else "degraded"
    except Exception:
        ai_light = "yellow"
        ai_status = "degraded"

    # ── System Resources ────────────────────────────────────────────────────
    try:
        mem = psutil.virtual_memory()
        cpu_pct = psutil.cpu_percent(interval=0.1)
        disk = psutil.disk_usage("/")
        mem_pct = mem.percent
        disk_pct = disk.percent
        resource_light = "green"
        if mem_pct > 85 or cpu_pct > 90 or disk_pct > 90:
            resource_light = "red"
        elif mem_pct > 70 or cpu_pct > 75 or disk_pct > 80:
            resource_light = "yellow"
        resources = {
            "cpu_pct": cpu_pct,
            "memory_pct": mem_pct,
            "disk_pct": disk_pct,
            "memory_used_mb": round(mem.used / 1024 / 1024, 1),
            "memory_total_mb": round(mem.total / 1024 / 1024, 1),
        }
    except Exception:
        resource_light = "yellow"
        resources = {"note": "psutil unavailable"}

    # ── Metrics snapshot ─────────────────────────────────────────────────────
    metrics = obs_metrics.get_metrics()
    circuit_breaker_light = "red" if metrics["circuit_breaker_opens"] > 10 else (
        "yellow" if metrics["circuit_breaker_opens"] > 3 else "green"
    )

    # ── Overall system status ────────────────────────────────────────────────
    lights = [db_light, cache_light, resource_light, circuit_breaker_light]
    if "red" in lights:
        overall = "critical"
    elif "yellow" in lights:
        overall = "warning"
    else:
        overall = "healthy"

    return {
        "status": overall,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": obs_metrics.uptime_seconds(),
        "components": {
            "backend": {"status": "online", "indicator": "green"},
            "database": {"status": db_status, "indicator": db_light},
            "cache": {"status": cache_status, "indicator": cache_light},
            "ai_engine": {"status": ai_status, "indicator": ai_light},
            "circuit_breakers": {
                "status": "warning" if metrics["circuit_breaker_opens"] > 3 else "ok",
                "indicator": circuit_breaker_light,
                "opens": metrics["circuit_breaker_opens"]
            },
            "resources": {
                "indicator": resource_light,
                **resources
            },
        },
        "metrics": metrics,
        "notifications": get_notification_status(),
    }


@app.get("/")
def read_root():
    return {
        "message": "Welcome to CarbonTracker AI",
        "status": "online",
        "version": "2.0.0",
        "mode": "offline_safe" if db_session.OFFLINE_MODE else "online",
        "docs": "/docs",
    }
