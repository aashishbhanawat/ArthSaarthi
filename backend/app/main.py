import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.middleware import SecurityHeadersMiddleware
from app.core.scheduler import shutdown_scheduler, start_scheduler
from app.db.init_db import run_db_migrations
from app.services.initialization_service import check_and_seed_on_startup

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

# Enable httpx/httpcore DEBUG logging ONLY when troubleshooting 429 errors.
# logging.getLogger("httpx").setLevel(logging.DEBUG)
# logging.getLogger("httpcore").setLevel(logging.DEBUG)

app = FastAPI(
    title="Personal Portfolio Management System",
    version="1.4.0",
    openapi_url="/api/v1/openapi.json",
)


@app.on_event("startup")
async def startup_event() -> None:
    # Run DB schema migrations and column auto-sync for upgraded databases
    try:
        run_db_migrations()
    except Exception as e:
        logging.error(f"Error during startup DB migrations: {e}", exc_info=True)

    try:
        check_and_seed_on_startup()
    except Exception as e:
        logging.error(f"Error during startup seeding check: {e}", exc_info=True)

    # Initialize and start Background Job Scheduler (FR17 / NFR14)
    try:
        start_scheduler()
    except Exception as e:
        logging.error(f"Error starting background job scheduler: {e}", exc_info=True)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    # Gracefully stop Background Job Scheduler
    try:
        shutdown_scheduler(wait=False)
    except Exception as e:
        logging.error(f"Error shutting down background job scheduler: {e}", exc_info=True)


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
