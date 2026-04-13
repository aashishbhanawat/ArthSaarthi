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

# Monkeypatch ForwardRef._evaluate for Python 3.12+ / Pydantic v1 compatibility
# This is only needed for newer Python versions that added the type_params argument.
if sys.version_info >= (3, 12):
    _original_evaluate = ForwardRef._evaluate
    def _patched_evaluate(self, globalns, localns, type_params=None, recursive_guard=frozenset()):
        return _original_evaluate(self, globalns, localns, type_params=type_params, recursive_guard=recursive_guard)
    ForwardRef._evaluate = _patched_evaluate

logger = logging.getLogger("arthsaarthi.android")
pid_file_path = None


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
        # Base.metadata.create_all is usually safe, but let's be explicit
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables verified/created.")
        except Exception as e:
            if "already exists" in str(e):
                logger.warning(f"Note: Table(s) already exist, skipping creation: {e}")
            else:
                raise
        
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

    # Enable httpx DEBUG logging to capture Yahoo Finance request/response headers.
    # yfinance >= 0.2 uses httpx/curl_cffi internally. This will dump all
    # outgoing request headers and incoming response status lines to logcat.
    # TODO: Remove or set to WARNING once debugging is complete.
    import logging as _logging
    _logging.getLogger("httpx").setLevel(_logging.DEBUG)
    _logging.getLogger("httpcore").setLevel(_logging.DEBUG)

    # Fix: Set certifi CA bundle so Python's SSL stack uses a known-good CA list.
    # Prevents crumb/cookie auth failure due to cert verification on Android's BoringSSL.
    try:
        import certifi
        os.environ["SSL_CERT_FILE"] = certifi.where()
        os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
        logger.info(f"SSL_CERT_FILE set to: {certifi.where()}")
    except ImportError:
        logger.warning("certifi not installed; SSL_CERT_FILE not set.")

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

    # Fix: point yfinance's tz cache to a writable Android directory.
    # Without this, yfinance may fail to write its cache and fall back to
    # unauthenticated requests, which Yahoo immediately rate-limits.
    try:
        import yfinance as yf
        yf_cache_dir = os.path.join(cache_dir, "yfinance_tz")
        os.makedirs(yf_cache_dir, exist_ok=True)
        yf.set_tz_cache_location(yf_cache_dir)
        logger.info(f"yfinance tz cache set to: {yf_cache_dir}")
    except Exception as e:
        logger.warning(f"Could not set yfinance tz cache: {e}")

    upload_dir = os.path.join(db_dir, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    os.environ["IMPORT_UPLOAD_DIR"] = upload_dir

    # Set a SECRET_KEY if not already set
    if "SECRET_KEY" not in os.environ:
        os.environ["SECRET_KEY"] = "android-local-secret-key-change-if-needed"

    logger.info(f"Database: {db_path}")

    # Singleton check using PID file
    global pid_file_path
    pid_file_path = os.path.join(db_dir, "backend.pid")
    port_file_path = os.path.join(db_dir, "backend.port")
    
    if os.path.exists(pid_file_path):
        try:
            with open(pid_file_path, "r") as f:
                old_pid = int(f.read().strip())
            
            # Check if the process is actually alive
            is_alive = False
            if old_pid == os.getpid():
                is_alive = True
            else:
                try:
                    os.kill(old_pid, 0)
                    is_alive = True
                except OSError:
                    pass

            if is_alive:
                logger.info(f"Backend already running (PID {old_pid}). Recovering port...")
                if os.path.exists(port_file_path):
                    try:
                        with open(port_file_path, "r") as f:
                            old_port = int(f.read().strip())
                        
                        # Re-notify Java/Android side of the existing port
                        from java import jclass
                        BackendService = jclass("com.arthsaarthi.app.BackendService")
                        BackendService.updatePort(old_port)
                        logger.info(f"Port {old_port} recovered and Java notified.")
                    except Exception as pe:
                        logger.error(f"Failed to recover port or notify Java: {pe}")
                
                if old_pid != os.getpid():
                    logger.warning("STALEMATE: Backend running in different process. Exiting.")
                    return
                else:
                    logger.info("Continuing within same process (previous thread likely dead or new Service lifecycle).")
            else:
                logger.info(f"Cleanup: Removing stale PID file for {old_pid}")
                os.remove(pid_file_path)
        except Exception as e:
            logger.error(f"Error during singleton check: {e}")

    with open(pid_file_path, "w") as f:
        f.write(str(os.getpid()))

    try:
        import uvicorn
        from app.main import app
        
        # Initialize the database (tables + base data)
        init_android_db()

        # Trigger background asset seeding if needed (Android specific)
        from app.services.initialization_service import check_and_seed_on_startup
        check_and_seed_on_startup()

        # Configure Uvicorn with more robust settings for Android
        config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=port,
            log_level="info",
            access_log=True,            # Enable for debugging exceptions/405s
            timeout_keep_alive=30,      # Increase keep-alive to handle flaky network
            timeout_graceful_shutdown=10,
            limit_concurrency=20,       # Prevent thread exhaustion on small devices
            backlog=100,
        )
        server = uvicorn.Server(config)

        # Ensure an event loop exists and is set for this thread
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
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
            
            # Persist port for recovery on app restart
            try:
                with open(os.path.join(os.environ["HOME"], ".arthsaarthi", "backend.port"), "w") as f:
                    f.write(str(actual_port))
            except Exception as pe:
                logger.error(f"Failed to persist port: {pe}")
            
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
    finally:
        if pid_file_path and os.path.exists(pid_file_path):
            try:
                os.remove(pid_file_path)
                logger.info("PID file removed.")
            except:
                pass
        
        # Attempt to close any remaining database connections
        try:
            from app.services.financial_data_service import financial_data_service
            financial_data_service.close()
            logger.info("FinancialDataService: session closed.")
        except:
            pass
        logger.info("Backend shutdown complete.")
