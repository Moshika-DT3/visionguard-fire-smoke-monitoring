"""FastAPI entry point for the standalone VisionGuard monitoring application."""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

# ---------------------------------------------------------------------------
# sys.path bootstrap
# ---------------------------------------------------------------------------
# ``backend`` is a regular Python package (see backend/__init__.py) and every
# module in this application imports its siblings using absolute
# ``backend.*`` import paths (for example ``from backend.models import ...``).
# This requires the repository root (the directory that *contains* the
# ``backend`` package) to be present on ``sys.path``.
#
# When the application is started with the documented command from the
# repository root, e.g.:
#   python -m uvicorn backend.main:app --reload
# Python automatically adds the current working directory (the repository
# root) to ``sys.path`` and everything resolves correctly.
#
# However, if this file is launched in a way that does not already include
# the repository root on ``sys.path`` -- for example by changing into the
# ``backend`` directory first and running ``uvicorn main:app`` or
# ``python main.py`` there -- Python instead adds the ``backend`` directory
# itself to ``sys.path``. In that situation the ``backend`` package can no
# longer be found as a top-level import, which raises:
#   ModuleNotFoundError: No module named 'backend'
#
# To make the application resilient to how it is launched, explicitly insert
# the repository root onto ``sys.path`` before importing any ``backend.*``
# module below. This is a no-op (and therefore safe) when the repository
# root is already importable.
_REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
if str(_REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPOSITORY_ROOT))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from backend.providers.mock import MockDetectionProvider
from backend.routers.api import create_api_router
from backend.routers.pages import create_page_router
from backend.services.monitoring import MonitoringService
from backend.services.video_analysis import YoloVideoAnalysisAdapter

BACKEND_DIRECTORY = Path(__file__).resolve().parent
# The frontend (Jinja2 templates and static assets) lives beside the backend package.
FRONTEND_DIRECTORY = BACKEND_DIRECTORY.parent / "frontend"
UPLOAD_DIRECTORY = BACKEND_DIRECTORY / "uploads"


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
video_analysis_adapter = YoloVideoAnalysisAdapter()
templates = Jinja2Templates(directory=str(FRONTEND_DIRECTORY / "templates"))

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
app.mount(
    "/static",
    StaticFiles(directory=str(FRONTEND_DIRECTORY / "static")),
    name="static",
)
app.include_router(create_page_router(templates, monitoring_service))
app.include_router(
    create_api_router(
        monitoring_service,
        video_analysis_adapter,
        UPLOAD_DIRECTORY,
    )
)
