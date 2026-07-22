from __future__ import annotations

import hmac
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

from agi_server.config import get_settings
from agi_server.db import SessionLocal, User

PUBLIC_API_PATHS = {
    "/api/health",
    "/api/openapi.json",
    "/api/setup/status",
    "/api/auth/bootstrap",
    "/api/auth/login",
}
CSRF_EXEMPT_PATHS = {"/api/auth/bootstrap", "/api/auth/login"}
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def error_response(request: Request, status_code: int, code: str, message: str) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": None,
                "request_id": request_id,
            }
        },
        headers={"X-Request-ID": request_id},
    )


class RequestSecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request.state.request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        settings = get_settings()
        path = request.url.path

        if path.startswith("/api") and request.method != "OPTIONS" and not settings.demo_no_auth:
            is_public = path in PUBLIC_API_PATHS or path.startswith("/api/docs") or path.startswith("/api/webhooks")
            if not is_public:
                user_id = request.session.get("user_id")
                with SessionLocal() as db:
                    user = db.get(User, user_id) if user_id else None
                if not user or not user.active:
                    request.session.clear()
                    return error_response(request, 401, "auth.required", "Oturum gerekli")
                request.state.user_id = user.id

            is_csrf_exempt = path in CSRF_EXEMPT_PATHS or path.startswith("/api/webhooks")
            if request.method not in SAFE_METHODS and not is_csrf_exempt:
                expected = request.session.get("csrf_token")
                supplied = request.headers.get("X-CSRF-Token")
                if not expected or not supplied or not hmac.compare_digest(expected, supplied):
                    return error_response(
                        request, 403, "csrf.invalid", "CSRF doğrulaması başarısız"
                    )

        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response
