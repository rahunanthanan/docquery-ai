"""DocQuery AI — FastAPI application entrypoint.

Task 2 scope: application factory, structlog request logging, and the
uniform error envelope (requirements §9). Feature routers (auth,
documents, qa, review, audit) are added in later tasks.
"""

import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.audit.router import router as audit_router
from app.auth.router import router as auth_router
from app.core.config import get_settings
from app.core.errors import AppError, error_envelope
from app.core.logging import configure_logging
from app.documents.router import router as documents_router
from app.qa.router import router as qa_router
from app.review.router import router as review_router
from app.usage.router import router as usage_router
from app.users.router import router as users_router

logger = structlog.get_logger()

# Router-level HTTPExceptions (unknown path, wrong method) get stable codes
# so clients never have to parse a second error shape.
_HTTP_ERROR_CODES = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}


def _error_response(request: Request, http_status: int, code: str, message: str) -> JSONResponse:
    request_id: str = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=http_status,
        content=error_envelope(code, message, request_id),
        headers={"X-Request-ID": request_id},
    )


async def _handle_app_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AppError)
    logger.warning("app_error", code=exc.code, http_status=exc.http_status, message=exc.message)
    return _error_response(request, exc.http_status, exc.code, exc.message)


async def _handle_http_exception(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    code = _HTTP_ERROR_CODES.get(exc.status_code, "HTTP_ERROR")
    return _error_response(request, exc.status_code, code, str(exc.detail))


async def _handle_validation_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    return _error_response(request, 422, "VALIDATION_FAILED", "Request validation failed.")


async def _handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    # Runs outside the middleware's contextvar scope, so request_id is
    # attached explicitly here.
    logger.exception(
        "unhandled_error",
        error_type=type(exc).__name__,
        request_id=getattr(request.state, "request_id", "unknown"),
    )
    return _error_response(request, 500, "INTERNAL_ERROR", "An unexpected error occurred.")


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    @app.middleware("http")
    async def request_context(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.state.request_id = request_id
        start = time.perf_counter()
        # user_id joins this bind once auth lands (Task 3).
        with structlog.contextvars.bound_contextvars(request_id=request_id):
            response = await call_next(request)
            logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                latency_ms=round((time.perf_counter() - start) * 1000, 2),
            )
        response.headers["X-Request-ID"] = request_id
        return response

    # Browser clients send the refresh cookie cross-origin (§3.3), so
    # credentials must be allowed and origins listed explicitly.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(documents_router)
    app.include_router(qa_router)
    app.include_router(review_router)
    app.include_router(audit_router)
    app.include_router(users_router)
    app.include_router(usage_router)

    app.add_exception_handler(AppError, _handle_app_error)
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(Exception, _handle_unexpected_error)

    @app.get("/api/v1/health", tags=["system"])
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "environment": settings.environment,
            "llm_provider": settings.llm_provider,
        }

    return app


app = create_app()
