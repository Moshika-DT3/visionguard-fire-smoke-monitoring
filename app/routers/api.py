"""JSON API routes for deterministic VisionGuard monitoring data."""

from __future__ import annotations

from fastapi import APIRouter

from app.models import CameraSource, DetectionEvent, MonitoringStatus
from app.services.monitoring import MonitoringService


# PUBLIC_INTERFACE
def create_api_router(monitoring_service: MonitoringService) -> APIRouter:
    """Create the JSON monitoring API backed by the service abstraction.

    Args:
        monitoring_service: Service supplying source-independent monitoring data.

    Returns:
        Router exposing health, camera-source, and detection-event endpoints.
    """
    router = APIRouter(prefix="/api", tags=["Monitoring API"])

    @router.get(
        "/health",
        response_model=MonitoringStatus,
        summary="Get VisionGuard health",
        description=(
            "Returns application status, active-source totals, and the current "
            "detection provider state."
        ),
    )
    async def health() -> MonitoringStatus:
        """Return the current application and Mock Detection Provider status."""
        return monitoring_service.get_system_status()

    @router.get(
        "/cameras",
        response_model=list[CameraSource],
        summary="List camera sources",
        description="Returns the deterministic sample camera inventory.",
    )
    async def cameras() -> list[CameraSource]:
        """Return all monitoring camera sources."""
        return list(monitoring_service.list_cameras())

    @router.get(
        "/events",
        response_model=list[DetectionEvent],
        summary="List detection events",
        description="Returns deterministic fire and smoke detection history.",
    )
    async def events() -> list[DetectionEvent]:
        """Return all detection events in stable newest-first order."""
        return list(monitoring_service.list_events())

    return router
