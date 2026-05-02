import logging

from alembic.config import Config
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from alembic import command
from app.core import config
from app.core import dependencies as deps
from app.db.base import Base  # Import Base with all models registered
from app.db.session import engine

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/reset-db", status_code=status.HTTP_204_NO_CONTENT)
def reset_db(
    db: Session = Depends(deps.get_db),
) -> Response:
    """
    Resets the database to a clean state for E2E testing.

    This endpoint is database-aware. For SQLite, it drops and recreates all tables
    directly from the models to avoid Alembic's limited support for ALTER TABLE.
    For PostgreSQL, it uses the standard Alembic downgrade/upgrade cycle.

    This endpoint is only available in a test environment and will raise a
    403 Forbidden error otherwise.
    """
    if config.settings.ENVIRONMENT != "test":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available in the test environment.",
        )

    logger.info(f"E2E: Resetting database (Type: {config.settings.DATABASE_TYPE})...")

    if config.settings.DATABASE_TYPE == "sqlite":
        # For SQLite, Alembic downgrades can fail due to limited ALTER TABLE support.
        # A robust reset is to drop and recreate all tables from the current models.
        logger.info("E2E: Using drop/create all for SQLite.")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        # After recreating, we need to stamp it again so the next test run doesn't fail.
        alembic_cfg = Config("alembic.ini")
        command.stamp(alembic_cfg, "head")
        logger.info("E2E: SQLite database reset and stamped successfully.")
    else:
        # For PostgreSQL, using Alembic is the correct way to ensure a clean schema.
        logger.info("E2E: Using alembic downgrade/upgrade for PostgreSQL.")
        try:
            alembic_cfg = Config("alembic.ini")
            command.downgrade(alembic_cfg, "base")
            command.upgrade(alembic_cfg, "head")
            logger.info("E2E: Database reset via Alembic successful.")
        except Exception as e:
            logger.error(f"E2E: Alembic command failed: {e}", exc_info=True)
            # Re-raise as an HTTPException to provide feedback to the test runner
            raise HTTPException(status_code=500, detail="Alembic command failed.")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/network-fingerprint")
def get_network_fingerprint():
    """
    Diagnostic endpoint to expose how Yahoo Finance (and other servers) "see"
    this backend's network identity.

    Returns:
    - ip: The outbound IP address (IPv4 or IPv6)
    - ja3_hash: The TLS fingerprint hash (JA3). If this differs between server
                and Android, it's the root cause of Android-specific 429s.
    - user_agent: The User-Agent string Python's http stack sends
    - ssl_version: The OpenSSL/BoringSSL version in use
    - platform: OS and Python version info

    Call this on BOTH server mode and Android mode and compare the ja3_hash.
    """
    import platform
    import ssl
    import sys

    import requests

    result = {
        "platform": {
            "os": platform.platform(),
            "python": sys.version,
            "openssl": ssl.OPENSSL_VERSION,
        },
        "tls_fingerprint": None,
        "ip_info": None,
        "error": None,
    }

    # 1. Grab TLS fingerprint (JA3 hash) from browserleaks
    try:
        resp = requests.get("https://tls.browserleaks.com/json", timeout=10)
        result["tls_fingerprint"] = resp.json()
    except Exception as e:
        result["error"] = f"tls.browserleaks.com failed: {e}"

    # 2. Get outbound IP (to detect IPv4 vs IPv6)
    try:
        ip_resp = requests.get("https://api64.ipify.org?format=json", timeout=10)
        result["ip_info"] = ip_resp.json()
    except Exception as e:
        result["ip_info"] = {"error": str(e)}

    logger.info("Network fingerprint: %s", result)
    return result


@router.get("/yfinance-diagnostic")
def yfinance_diagnostic():
    """
    Full yfinance diagnostic endpoint (equivalent to yf_debug.py).
    Run on BOTH server and Android to compare environments.
    Key output: ja3_hash, openssl version, cipher count, HTTP status from Yahoo.
    """
    import platform
    import ssl
    import sys

    import requests

    out = {}

    # 1. Platform & SSL info
    ctx = ssl.create_default_context()
    ciphers = ctx.get_ciphers()
    out["environment"] = {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": sys.version.split()[0],
        "openssl": ssl.OPENSSL_VERSION,
        "cipher_count": len(ciphers),
        "cipher_list_first_10": [c["name"] for c in ciphers[:10]],
        "ssl_cert_file": __import__("os").environ.get("SSL_CERT_FILE", "not set"),
    }

    # 1b. DNS / IP Raw Connectivity Check
    import socket
    try:
        # Test raw IP connectivity (Cloudflare DNS)
        socket.create_connection(("1.1.1.1", 53), timeout=3).close()
        out["network_raw"] = "OK (Reached 1.1.1.1:53)"
    except Exception as e:
        out["network_raw"] = f"FAILED: {e}"

    try:
        # Test DNS resolution directly
        out["dns_lookup_google"] = socket.gethostbyname("google.com")
    except Exception as e:
        out["dns_lookup_google"] = f"FAILED: {e}"

    # 2. requests / certifi info
    try:
        import certifi
        out["certifi"] = certifi.__version__
    except ImportError:
        out["certifi"] = "NOT INSTALLED"

    try:
        import curl_cffi
        out["curl_cffi"] = curl_cffi.__version__
    except ImportError:
        out["curl_cffi"] = "NOT INSTALLED"

    # 3. JA3 fingerprint (Python requests, not curl)
    try:
        r = requests.get("https://tls.browserleaks.com/json", timeout=12)
        out["ja3"] = {
            "ja3_hash": r.json().get("ja3_hash"),
            "ja4": r.json().get("ja4"),
            "user_agent_seen": r.json().get("user_agent"),
        }
    except Exception as e:
        out["ja3"] = {"error": str(e)}

    # 4. Outbound IP
    try:
        ip_r = requests.get("https://api64.ipify.org?format=json", timeout=10)
        out["ip"] = ip_r.json()
    except Exception as e:
        out["ip"] = {"error": str(e)}

    # 5. Direct Yahoo Finance API request — check status code
    test_url = "https://query1.finance.yahoo.com/v8/finance/chart/NTPC.NS?range=1d&interval=1d"
    for label, headers in [
        ("default_ua", {}),
        ("spoof", {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
        }),
    ]:
        try:
            resp = requests.get(
                test_url, headers=headers, timeout=12, allow_redirects=False
            )
            out[f"yahoo_{label}"] = {
                "status": resp.status_code,
                "retry_after": resp.headers.get("Retry-After"),
                "x_ratelimit": resp.headers.get("x-ratelimit-remaining"),
                "cf_mitigated": resp.headers.get("cf-mitigated"),
                "body_preview": resp.text[:200],
            }
        except Exception as e:
            out[f"yahoo_{label}"] = {"error": str(e)}

    # 6. yfinance version and cache location
    try:
        import yfinance as yf
        out["yfinance"] = {"version": yf.__version__}
        try:
            loc = (
                yf.cache.get_tz_cache_location()
                if hasattr(yf, "cache")
                else "unknown"
            )
            out["yfinance"]["tz_cache"] = str(loc)
        except Exception:
            pass
    except Exception as e:
        out["yfinance"] = {"error": str(e)}

    logger.info("yfinance diagnostic complete")
    return out
