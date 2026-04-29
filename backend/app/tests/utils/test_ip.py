from fastapi import Request

from app.utils.ip import get_client_ip


def test_get_client_ip_cf_connecting_ip():
    request = Request(
        {"type": "http", "headers": [(b"cf-connecting-ip", b"203.0.113.1")]}
    )
    assert get_client_ip(request) == "203.0.113.1"

def test_get_client_ip_x_forwarded_for():
    request = Request(
        {"type": "http", "headers": [(b"x-forwarded-for", b"203.0.113.2, 198.51.1")]}
    )
    assert get_client_ip(request) == "203.0.113.2"

def test_get_client_ip_x_real_ip():
    request = Request({"type": "http", "headers": [(b"x-real-ip", b"203.0.113.3")]})
    assert get_client_ip(request) == "203.0.113.3"

def test_get_client_ip_fallback():
    request = Request({"type": "http", "headers": [], "client": ("203.0.113.4", 8080)})
    assert get_client_ip(request) == "203.0.113.4"

def test_get_client_ip_no_client():
    request = Request({"type": "http", "headers": []})
    assert get_client_ip(request) == "127.0.0.1"
