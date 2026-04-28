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

# File handler (desktop mode only)
if settings.DEPLOYMENT_MODE == "desktop":
    log_dir = Path.home() / ".arthsaarthi" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "arthsaarthi.log"

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

    logging.info(f"Desktop mode: Logging to {log_file}")
# --- End Logging Configuration ---

app = FastAPI(
    title="Personal Portfolio Management System",
    openapi_url="/api/v1/openapi.json",
)

@app.on_event("startup")
async def startup_event() -> None:
    global _snapshot_task
    if settings.DEPLOYMENT_MODE == "desktop":
        logging.info("Spawning background snapshot task for Desktop App...")
        _snapshot_task = asyncio.create_task(_desktop_snapshot_loop())

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
