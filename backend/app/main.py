import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.api import api_router
from app.core.config import settings

app = FastAPI(
    title="Personal Portfolio Management System",
    openapi_url="/api/v1/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    # Use the origins from the settings
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

# This part should be last, as it includes a catch-all route.
if settings.SERVE_STATIC_FRONTEND:
    # The directory where the built frontend assets are located.
    # This is configured to be 'static' and will be the output dir of the
    # frontend build.
    static_files_dir = os.path.join(os.path.dirname(__file__), "..", "static")

    # Serve the static files (JS, CSS, images) and handle client-side routing.
    app.mount("/", StaticFiles(directory=static_files_dir, html=True), name="static")
