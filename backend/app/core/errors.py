"""Central exception hierarchy and error envelope (requirements §9).

Services raise these; the exception handlers in `app.main` convert them
into the single uniform envelope every API error uses:

    {"error": {"code": "...", "message": "...", "requestId": "..."}}
"""


class AppError(Exception):
    """Base class for expected application failures.

    Subclasses fix `code` and `http_status`. `code` may be narrowed per
    instance for more specific client handling, e.g.
    ``NotFoundError("...", code="DOCUMENT_NOT_FOUND")``.
    """

    code: str = "APP_ERROR"
    http_status: int = 500

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code


class NotFoundError(AppError):
    code = "NOT_FOUND"
    http_status = 404


class PermissionDeniedError(AppError):
    code = "PERMISSION_DENIED"
    http_status = 403


class ValidationFailed(AppError):
    code = "VALIDATION_FAILED"
    http_status = 422


class InvalidTransition(AppError):
    code = "INVALID_TRANSITION"
    http_status = 409


class LLMProviderError(AppError):
    code = "LLM_UNAVAILABLE"
    http_status = 502


class QuotaExceeded(AppError):
    code = "QUOTA_EXCEEDED"
    http_status = 429


def error_envelope(code: str, message: str, request_id: str) -> dict[str, dict[str, str]]:
    return {"error": {"code": code, "message": message, "requestId": request_id}}
