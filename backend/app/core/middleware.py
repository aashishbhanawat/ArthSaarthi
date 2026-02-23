"""Security headers middleware for FastAPI."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds standard security headers to all HTTP responses.

    Headers:
    - X-Content-Type-Options: Prevents MIME sniffing
    - X-Frame-Options: Prevents clickjacking
    - X-XSS-Protection: Legacy XSS filter (still useful for older browsers)
    - Referrer-Policy: Controls referrer information leakage
    - Content-Security-Policy: Mitigates XSS and other attacks
    - Strict-Transport-Security: HSTS (production only)
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers[
            "Referrer-Policy"
        ] = "strict-origin-when-cross-origin"

        # Content Security Policy
        # default-src 'self': Only allow resources from the same origin by default
        # script-src: Allow self, unsafe-inline (needed for Swagger UI), and CDNs (Swagger UI assets)
        # style-src: Allow self, unsafe-inline (needed for Swagger UI), and CDNs
        # img-src: Allow self, data: (for base64 images), CDNs, and fastapi.tiangolo.com (Swagger UI favicon)
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://fastapicdn.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fastapicdn.com; "
            "img-src 'self' data: https://cdn.jsdelivr.net https://fastapi.tiangolo.com; "
            "font-src 'self' data: https://cdn.jsdelivr.net https://fastapicdn.com; "
            "connect-src 'self'; "
            "object-src 'none'; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp_policy

        # Only enable HSTS in production (requires HTTPS)
        if settings.ENVIRONMENT == "production":
            response.headers[
                "Strict-Transport-Security"
            ] = "max-age=63072000; includeSubDomains"

        return response
