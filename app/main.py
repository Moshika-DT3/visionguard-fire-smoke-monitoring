"""FastAPI entry point for the standalone VisionGuard monitoring application."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.providers.mock import MockDetectionProvider
from app.routers.api import create_api_router
from app.routers.pages import create_page_router
from app.services.monitoring import MonitoringService

APP_DIRECTORY = Path(__file__).resolve().parent

# Provider composition boundary: replace this implementation with a future
# VisionAI adapter that satisfies DetectionProvider without changing routes or UI.
provider = MockDetectionProvider()
monitoring_service = MonitoringService(provider)
templates = Jinja2Templates(directory=str(APP_DIRECTORY / "templates"))

app = FastAPI(
    title="VisionGuard - Fire & Smoke Monitoring",
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
app.include_router(create_api_router(monitoring_service))
