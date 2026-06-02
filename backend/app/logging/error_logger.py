import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.utils.logger import log_structured_error

def setup_error_logging(app: FastAPI):
    """
    Registers a global exception handler to catch all unhandled errors,
    log full traceback details to structured log,
    and return standardized user-safe error responses.
    """
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        endpoint = request.url.path
        method = request.method
        
        # Read the request body payload safely
        payload = None
        try:
            body = await request.body()
            if body:
                payload = body.decode("utf-8", errors="ignore")
        except Exception as e:
            pass
            
        # Log structured error message
        log_structured_error(
            service="global_exception_handler",
            severity="error",
            message=f"Unhandled exception intercept on {method} {endpoint}. Payload: {payload}. Error: {str(exc)}",
            error=exc
        )
        
        # Return standardized frontend-safe error envelope
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "data": {},
                "error": "An unexpected internal error occurred. Please try again later."
            }
        )
