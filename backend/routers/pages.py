"""Server-rendered Jinja2 pages for VisionGuard monitoring views."""

from __future__ import annotations

from fastapi import APIRouter, Query, Request
from fastapi.templating import Jinja2Templates

from backend.services.monitoring import MonitoringService

router = APIRouter(tags=["Monitoring pages"])


# PUBLIC_INTERFACE
def create_page_router(
    templates: Jinja2Templates,
    monitoring_service: MonitoringService,
) -> APIRouter:
    """Create page routes backed by a source-independent monitoring service.

    Args:
        templates: Configured Jinja2 template environment.
        monitoring_service: Service supplying dashboard and monitoring data.

    Returns:
        Router containing all server-rendered VisionGuard page routes.
    """

    @router.get(
        "/",
        summary="Render the VisionGuard dashboard",
        description="Displays deterministic monitoring metrics and recent detection events.",
    )
    async def dashboard(request: Request):
        """Render the main VisionGuard monitoring dashboard."""
        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "metrics": monitoring_service.get_metrics(),
                "system_status": monitoring_service.get_system_status(),
                "recent_events": monitoring_service.get_recent_events(),
            },
        )

    @router.get(
        "/cameras",
        summary="Render camera sources",
        description="Displays the configured sample camera inventory.",
    )
    async def cameras(request: Request):
        """Render the source inventory page."""
        return templates.TemplateResponse(
            request=request,
            name="cameras.html",
            context={"cameras": monitoring_service.list_cameras()},
        )

    @router.get(
        "/incidents",
        summary="Render incident history",
        description="Displays historical detection events filtered by all, fire, or smoke.",
    )
    async def incidents(
        request: Request,
        type: str = Query(
            default="all",
            description="Incident type filter: all, fire, or smoke.",
        ),
    ):
        """Render incident history with a safe normalized event-type filter."""
        selected_type = type.lower()
        if selected_type not in {"all", "fire", "smoke"}:
            selected_type = "all"
        return templates.TemplateResponse(
            request=request,
            name="incidents.html",
            context={
                "events": monitoring_service.list_events(selected_type),
                "selected_type": selected_type,
            },
        )

    @router.get(
        "/video-testing",
        summary="Render Video Testing",
        description=(
            "Displays local MP4 upload, browser preview, and deterministic "
            "mock-analysis workflow validation."
        ),
    )
    async def video_testing(request: Request):
        """Render the Video Testing page without changing monitoring workflows."""
        return templates.TemplateResponse(
            request=request,
            name="video_testing.html",
            context={},
        )

    @router.get(
        "/status",
        summary="Render system status",
        description="Displays the application and active detection provider status.",
    )
    async def status(request: Request):
        """Render the operational system status page."""
        return templates.TemplateResponse(
            request=request,
            name="status.html",
            context={"system_status": monitoring_service.get_system_status()},
        )

    return router
