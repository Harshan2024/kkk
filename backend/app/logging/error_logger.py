import logging
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("carbontracker.errors")

def setup_error_logging(app: FastAPI):
    """
    Registers a global exception handler to catch all unhandled errors,
    log full traceback details, request payload, and endpoint paths,
    and return standardized frontend-safe error structures.
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
            logger.error(f"Failed to read request body payload: {str(e)}")
            
        tb = traceback.format_exc()
        
        # Centralized logging of the exception
        logger.error(
            f"--- 500 INTERNAL SERVER ERROR INTERCEPTED ---\n"
            f"Endpoint: {endpoint}\n"
            f"Method: {method}\n"
            f"Payload: {payload}\n"
            f"Error Type: {type(exc).__name__}\n"
            f"Error Details: {str(exc)}\n"
            f"Traceback:\n{tb}"
        )
        
        # Return standard API structure
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "data": {},
                "error": f"Internal Server Error: {str(exc)}"
            }
        )
