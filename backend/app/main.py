import asyncio
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.middleware import SecurityHeadersMiddleware
from app.db.session import SessionLocal
from app.services.snapshot_service import take_daily_snapshots_for_all

# --- Background Task for Desktop App ---
_snapshot_task: Optional[asyncio.Task] = None

async def _desktop_snapshot_loop() -> None:
    """
    Background loop that runs only in Desktop mode.
    It takes a snapshot on startup, then sleeps and wakes up periodically
    (e.g., every 6 hours) to take another snapshot.
    """
    await asyncio.sleep(10)  # Give the server a moment to fully start

    while True:
        logging.info("Running desktop background snapshot check...")
        db = SessionLocal()
        try:
            # We run the blocking DB operations in a threadpool so it doesn't
            # block the main asyncio event loop.
            loop = asyncio.get_running_loop()
            count = await loop.run_in_executor(None, take_daily_snapshots_for_all, db)
            logging.info(f"Desktop snapshot check completed. {count} updated.")
        except Exception as e:
            logging.error(f"Error in desktop background snapshot loop: {e}")
        finally:
            db.close()

        # Sleep for 6 hours (21600 seconds)
        await asyncio.sleep(21600)

# --- Logging Configuration ---
log_level = logging.DEBUG if settings.DEBUG else logging.INFO
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(log_level)

# Console handler (always)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter(log_format))
root_logger.addHandler(console_handler)

# File handler (desktop and android mode)
if settings.DEPLOYMENT_MODE in ("desktop", "android") and settings.LOG_FILE:
    log_file = Path(settings.LOG_FILE)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,  # Keep 3 backup files
    )
    file_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(file_handler)

    # Also add file handler to uvicorn loggers for HTTP request logging
    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.addHandler(file_handler)

    logging.info(f"{settings.DEPLOYMENT_MODE.capitalize()} mode: Logging to {log_file}")
# --- End Logging Configuration ---

app = FastAPI(
    title="Personal Portfolio Management System",
    version="1.2.0",
    openapi_url="/api/v1/openapi.json",
)

@app.on_event("startup")
async def startup_event() -> None:
    global _snapshot_task
    if settings.DEPLOYMENT_MODE in ("desktop", "android"):
        logging.info(f"Spawning background snapshot task for {settings.DEPLOYMENT_MODE.capitalize()} App...")
        _snapshot_task = asyncio.create_task(_desktop_snapshot_loop())
        
        # Trigger background asset seeding if database is empty
        from app.services.initialization_service import check_and_seed_on_startup
        check_and_seed_on_startup()

app.add_middleware(
    CORSMiddleware,
    # Use the origins from the settings
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SecurityHeadersMiddleware)

app.include_router(api_router, prefix="/api/v1")
