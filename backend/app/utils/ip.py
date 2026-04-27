from fastapi import Request


def get_client_ip(request: Request) -> str:
    """
    Extracts the real client IP address from the request, prioritizing proxy headers.
    This is essential for applications deployed behind Cloudflare, Nginx, etc.
    """
    if "cf-connecting-ip" in request.headers:
        return request.headers["cf-connecting-ip"]

    if "x-forwarded-for" in request.headers:
        # X-Forwarded-For can be a comma-separated list of IPs.
        # The client's original IP is the first one.
        x_forwarded_for = request.headers["x-forwarded-for"]
        return x_forwarded_for.split(",")[0].strip()

    if "x-real-ip" in request.headers:
        return request.headers["x-real-ip"]

    return request.client.host if request.client else "127.0.0.1"
