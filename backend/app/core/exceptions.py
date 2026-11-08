"""Domain exceptions and centralised exception handlers.

Every error response uses one envelope:
    {"error": {"code": str, "message": str, "details": any | null, "request_id": str}}
Error codes are UPPER_SNAKE_CASE.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import request_id_ctx

logger = logging.getLogger(__name__)


class AppError(Exception):
    status_code = 500
    code = "INTERNAL_ERROR"

    def __init__(self, message: str = "Internal server error", *, details: Any = None, code: str | None = None):
        super().__init__(message)
        self.message = message
        self.details = details
        if code:
            self.code = code


class BadRequestError(AppError):
    status_code, code = 400, "BAD_REQUEST"


class UnauthorizedError(AppError):
    status_code, code = 401, "UNAUTHORIZED"


class AuthenticationError(UnauthorizedError):
    code = "AUTHENTICATION_FAILED"


class ForbiddenError(AppError):
    status_code, code = 403, "FORBIDDEN"


class PermissionDeniedError(ForbiddenError):
    code = "PERMISSION_DENIED"


class NotFoundError(AppError):
    status_code, code = 404, "NOT_FOUND"


class ConflictError(AppError):
    status_code, code = 409, "CONFLICT"


class BusinessRuleError(AppError):
    status_code, code = 422, "BUSINESS_RULE_VIOLATION"


class ServiceUnavailableError(AppError):
    status_code, code = 503, "SERVICE_UNAVAILABLE"


def _body(code: str, message: str, details: Any = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details, "request_id": request_id_ctx.get()}}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        if exc.status_code >= 500:
            logger.error("AppError %s: %s", exc.code, exc.message)
        headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
        return JSONResponse(
            status_code=exc.status_code, content=_body(exc.code, exc.message, exc.details), headers=headers
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {"loc": list(e["loc"]), "msg": e["msg"], "type": e["type"]} for e in exc.errors()
        ]
        return JSONResponse(status_code=422, content=_body("VALIDATION_ERROR", "Request validation failed", details))

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}.get(exc.status_code, "HTTP_ERROR")
        return JSONResponse(
            status_code=exc.status_code,
            content=_body(code, str(exc.detail)),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc)
        # Never leak internals to the client.
        return JSONResponse(status_code=500, content=_body("INTERNAL_ERROR", "Internal server error"))