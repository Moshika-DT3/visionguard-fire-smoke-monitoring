"""Application service that transforms provider records into monitoring views."""

from __future__ import annotations

from typing import Sequence

from app.models import (
    CameraSource,
    CameraStatus,
    DashboardMetrics,
    DetectionEvent,
    EventType,
    MonitoringStatus,
)
from app.providers.base import DetectionProvider


class MonitoringService:
    """Expose source-independent monitoring queries to web and API routes."""

    def __init__(self, provider: DetectionProvider) -> None:
        """Store the provider contract used for all monitoring data access."""
        self._provider = provider

    def list_cameras(self) -> Sequence[CameraSource]:
        """Return all configured camera sources."""
        return self._provider.list_cameras()

    def list_events(self, event_type: str = "all") -> Sequence[DetectionEvent]:
        """Return all events or events matching a supported hazard filter."""
        events = self._provider.list_events()
        normalized_type = event_type.lower()
        if normalized_type == EventType.FIRE.value:
            return tuple(event for event in events if event.event_type is EventType.FIRE)
        if normalized_type == EventType.SMOKE.value:
            return tuple(event for event in events if event.event_type is EventType.SMOKE)
        return events

    def get_recent_events(self, limit: int = 4) -> Sequence[DetectionEvent]:
        """Return the newest deterministic events for the dashboard."""
        return self._provider.list_events()[:limit]

    def get_metrics(self) -> DashboardMetrics:
        """Calculate dashboard counters from the provider's stable data."""
        cameras = self._provider.list_cameras()
        events = self._provider.list_events()
        return DashboardMetrics(
            active_cameras=sum(
                camera.status is CameraStatus.ACTIVE for camera in cameras
            ),
            total_incidents=len(events),
            fire_alerts=sum(event.event_type is EventType.FIRE for event in events),
            smoke_alerts=sum(event.event_type is EventType.SMOKE for event in events),
        )

    def get_system_status(self) -> MonitoringStatus:
        """Build VisionGuard and provider status for pages and health API."""
        cameras = self._provider.list_cameras()
        active_sources = sum(
            camera.status is CameraStatus.ACTIVE for camera in cameras
        )
        return MonitoringStatus(
            application_status="Operational",
            provider=self._provider.get_provider_status(),
            active_sources=active_sources,
            total_sources=len(cameras),
        )
