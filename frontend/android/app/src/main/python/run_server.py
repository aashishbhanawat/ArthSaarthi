"""
Android entry point for the ArthSaarthi FastAPI backend.

This module is invoked by Chaquopy from the Android native layer.
It starts the FastAPI/Uvicorn server on a given port, using the
Android app's internal filesDir for SQLite database and cache storage.
"""
import os
import sys
import logging
from typing import ForwardRef

# Monkeypatch ForwardRef._evaluate for Python 3.13 / Pydantic v1 compatibility
_original_evaluate = ForwardRef._evaluate
def _patched_evaluate(self, globalns, localns, type_params=None, recursive_guard=frozenset()):
    return _original_evaluate(self, globalns, localns, type_params=type_params, recursive_guard=recursive_guard)
ForwardRef._evaluate = _patched_evaluate

logger = logging.getLogger("arthsaarthi.android")


def start(port: int, data_dir: str):
    """
    Start the FastAPI backend server.

    Args:
        port: The port to bind the server to (assigned by Android).
        data_dir: The Android app's internal data directory (filesDir).
                  The SQLite database and disk cache will be stored here.
    """
    # Set environment variables before importing the app
    os.environ["DEPLOYMENT_MODE"] = "android"
    os.environ["DATABASE_TYPE"] = "sqlite"
    os.environ["CACHE_TYPE"] = "disk"
    os.environ["DEBUG"] = "false"
    os.environ["LOG_LEVEL"] = "INFO"

    # Critically, set HOME so Path.home() works for logging
    os.environ["HOME"] = data_dir
    print(f"PYTHON: Setting HOME to {data_dir}")

    # Set up data paths
    db_dir = os.path.join(data_dir, "arthsaarthi")
    os.makedirs(db_dir, exist_ok=True)

    # Also create the log directory that main.py expects
    log_dir = os.path.join(db_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    os.environ["HOME"] = data_dir
    os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(db_dir, 'arthsaarthi.db')}"

    cache_dir = os.path.join(db_dir, "cache")
    os.makedirs(cache_dir, exist_ok=True)
    os.environ["DISK_CACHE_DIR"] = cache_dir

    upload_dir = os.path.join(db_dir, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    os.environ["IMPORT_UPLOAD_DIR"] = upload_dir

    # Set a SECRET_KEY if not already set
    if "SECRET_KEY" not in os.environ:
        os.environ["SECRET_KEY"] = "android-local-secret-key-change-if-needed"

    logger.info(f"Starting ArthSaarthi backend on port {port}")
    logger.info(f"Data directory: {data_dir}")
    logger.info(f"Database: {db_path}")

    try:
        import uvicorn
        from app.main import app

        # Run Uvicorn — this blocks until the server is stopped
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=port,
            log_level="info",
            # Disable reload on Android (no file watching needed)
            # Disable access log to reduce overhead on mobile
            access_log=False,
        )
    except Exception as e:
        logger.error(f"Failed to start backend: {e}", exc_info=True)
        raise
