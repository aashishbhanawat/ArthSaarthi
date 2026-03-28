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


def init_android_db():
    """
    Initializes the SQLite database on Android.
    Matches the logic in entrypoint.sh and app.cli:init-db.
    """
    from app.db.base import Base
    from app.db.session import engine, SessionLocal
    from app.db.initial_data import seed_interest_rates
    
    logger.info("Initializing Android SQLite database tables...")
    try:
        # Create all tables if they don't exist
        Base.metadata.create_all(bind=engine)
        
        # Seed initial data (like interest rates)
        db = SessionLocal()
        try:
            seed_interest_rates(db)
            db.commit()
            logger.info("Initial data seeded (interest rates).")
        finally:
            db.close()
            
        logger.info("Database initialization complete.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)


def start(port: int, data_dir: str):
    """
    Start the FastAPI backend server.

    Args:
        port: The port to bind the server to. Use 0 for dynamic selection.
        data_dir: The Android app's internal data directory (filesDir).
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
    db_dir = os.path.join(data_dir, ".arthsaarthi")
    os.makedirs(db_dir, exist_ok=True)

    # Also create the log directory that main.py expects
    log_dir = os.path.join(db_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "arthsaarthi.db")
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    cache_dir = os.path.join(db_dir, "cache")
    os.makedirs(cache_dir, exist_ok=True)
    os.environ["DISK_CACHE_DIR"] = cache_dir

    upload_dir = os.path.join(db_dir, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    os.environ["IMPORT_UPLOAD_DIR"] = upload_dir

    # Set a SECRET_KEY if not already set
    if "SECRET_KEY" not in os.environ:
        os.environ["SECRET_KEY"] = "android-local-secret-key-change-if-needed"

    logger.info(f"Preparing ArthSaarthi backend on Android")
    logger.info(f"Data directory: {data_dir}")
    logger.info(f"Database: {db_path}")

    try:
        import uvicorn
        from app.main import app
        
        # Initialize the database (tables + base data)
        init_android_db()

        # Configure Uvicorn
        config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=port,
            log_level="info",
            access_log=False,
        )
        server = uvicorn.Server(config)

        # Use uvicorn's startup sequence to get the actual port and notify Java
        import asyncio
        loop = asyncio.get_event_loop()
        
        # Override the server's startup to notify Java about the port
        original_startup = server.startup
        
        async def patched_startup(sockets=None):
            await original_startup(sockets=sockets)
            # Find the actual port we bound to
            actual_port = port
            for server_obj in server.servers:
                for socket in server_obj.sockets:
                    actual_port = socket.getsockname()[1]
                    break
            
            logger.info(f"Uvicorn bound to port: {actual_port}")
            
            # Notify Java/Android side
            try:
                from java import jclass
                BackendService = jclass("com.arthsaarthi.app.BackendService")
                BackendService.updatePort(actual_port)
            except Exception as e:
                logger.error(f"Failed to notify Java about port {actual_port}: {e}")

        server.startup = patched_startup

        # Run the server (this blocks)
        loop.run_until_complete(server.serve())

    except Exception as e:
        logger.error(f"Failed to start backend: {e}", exc_info=True)
        raise
