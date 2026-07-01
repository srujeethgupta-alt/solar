import json
import traceback
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.logger import setup_logger

logger = setup_logger("exceptions")

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            body = None
            if request.method in ("POST", "PUT", "PATCH"):
                try:
                    body = await request.json()
                except json.JSONDecodeError:
                    return JSONResponse(
                        status_code=400,
                        content={"detail": "Invalid JSON in request body"}
                    )
                except Exception:
                    pass
            response = await call_next(request)
            return response
        except Exception as e:
            logger.exception(f"Unhandled exception on {request.method} {request.url.path}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error. Please try again later."}
            )

def register_exception_handlers(app):
    @app.exception_handler(500)
    async def internal_error(request, exc):
        logger.exception(f"500 error on {request.method} {request.url.path}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

    @app.exception_handler(404)
    async def not_found(request, exc):
        return JSONResponse(
            status_code=404,
            content={"detail": "Resource not found"}
        )

    @app.exception_handler(405)
    async def method_not_allowed(request, exc):
        return JSONResponse(
            status_code=405,
            content={"detail": "Method not allowed"}
        )
