from unittest import mock

from app.core.config import settings


def test_security_headers_production(client):
    """
    Verify that security headers are present in production environment.
    """
    with mock.patch.object(settings, "ENVIRONMENT", "production"):
        response = client.get("/api/v1/auth/status")
        assert response.status_code == 200
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert (
            response.headers["Strict-Transport-Security"]
            == "max-age=63072000; includeSubDomains"
        )


def test_security_headers_non_production(client):
    """
    Verify that HSTS header is NOT present in non-production environment.
    """
    with mock.patch.object(settings, "ENVIRONMENT", "test"):
        response = client.get("/api/v1/auth/status")
        assert response.status_code == 200
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert "Strict-Transport-Security" not in response.headers
