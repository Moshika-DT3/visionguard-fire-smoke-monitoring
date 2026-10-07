"""FastAPI entry point for the standalone VisionGuard monitoring application."""

from __future__ import annotations

from contextlib import asynccontextmanager
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.providers.mock import MockDetectionProvider
from app.routers.api import DEFAULT_MAX_UPLOAD_BYTES, create_api_router
from app.routers.pages import create_page_router
from app.services.monitoring import MonitoringService
from app.services.video_analysis import MockVideoAnalysisAdapter

APP_DIRECTORY = Path(__file__).resolve().parent
UPLOAD_DIRECTORY = APP_DIRECTORY / "uploads"

# Optional VIDEO_UPLOAD_MAX_BYTES can be requested from the user for .env setup.
MAX_UPLOAD_BYTES = int(os.environ.get("VIDEO_UPLOAD_MAX_BYTES", DEFAULT_MAX_UPLOAD_BYTES))


def _cleanup_demo_uploads() -> None:
    """Remove generated MP4s only, leaving unrelated files and symlinks alone."""
    for path in UPLOAD_DIRECTORY.glob("*.mp4"):
        if (
            len(path.stem) == 32
            and all(character in "0123456789abcdef" for character in path.stem)
            and not path.is_symlink()
            and path.is_file()
        ):
            path.unlink()


# PUBLIC_INTERFACE
@asynccontextmanager
async def lifespan(application: FastAPI):
    """Manage demo upload retention for ``application``; yield while it runs.

    Startup removes leftovers from interrupted sessions; shutdown removes the
    current session's generated uploads. Run one local application process.
    """
    _cleanup_demo_uploads()
    try:
        yield
    finally:
        _cleanup_demo_uploads()


# Provider composition boundary: replace this implementation with a future
# VisionAI adapter that satisfies DetectionProvider without changing routes or UI.
provider = MockDetectionProvider()
monitoring_service = MonitoringService(provider)
video_analysis_adapter = MockVideoAnalysisAdapter()
templates = Jinja2Templates(directory=str(APP_DIRECTORY / "templates"))

app = FastAPI(
    title="VisionGuard - Fire & Smoke Monitoring",
    lifespan=lifespan,
    description=(
        "Standalone deterministic fire and smoke monitoring baseline powered by "
        "the Mock Detection Provider."
    ),
    version="0.1.0",
    openapi_tags=[
        {
            "name": "Monitoring pages",
            "description": "Server-rendered operational monitoring pages.",
        },
        {
            "name": "Monitoring API",
            "description": "Read-only JSON endpoints backed by deterministic data.",
        },
    ],
)
app.mount("/static", StaticFiles(directory=str(APP_DIRECTORY / "static")), name="static")
app.include_router(create_page_router(templates, monitoring_service))
app.include_router(
    create_api_router(
        monitoring_service,
        video_analysis_adapter,
        UPLOAD_DIRECTORY,
        max_upload_bytes=MAX_UPLOAD_BYTES,
    )
)
