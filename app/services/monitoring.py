"""Application service that transforms provider records into monitoring views."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence

from app.models import (
    CameraSource,
    CameraStatus,
    DashboardMetrics,
    DetectionEvent,
    EventType,
    MonitoringStatus,
    Severity,
    VideoAnalysisOutcome,
)
from app.providers.base import DetectionProvider


class MonitoringService:
    """Expose source-independent monitoring queries to web and API routes."""

    def __init__(self, provider: DetectionProvider) -> None:
        """Store the provider contract and session-local generated events."""
        self._provider = provider
        self._video_events: list[DetectionEvent] = []
        self._analyzed_video_names: set[str] = set()

    def list_cameras(self) -> Sequence[CameraSource]:
        """Return all configured camera sources."""
        return self._provider.list_cameras()

    def list_events(self, event_type: str = "all") -> Sequence[DetectionEvent]:
        """Return all events or events matching a supported hazard filter."""
        events = (*self._video_events, *self._provider.list_events())
        normalized_type = event_type.lower()
        if normalized_type == EventType.FIRE.value:
            return tuple(event for event in events if event.event_type is EventType.FIRE)
        if normalized_type == EventType.SMOKE.value:
            return tuple(event for event in events if event.event_type is EventType.SMOKE)
        return events

    def get_recent_events(self, limit: int = 4) -> Sequence[DetectionEvent]:
        """Return the newest events, including current-session video detections."""
        return self.list_events()[:limit]

    def create_video_incident(
        self,
        filename: str,
        outcome: VideoAnalysisOutcome,
        confidence: float,
    ) -> bool:
        """Create one event for a positive video result unless already analyzed.

        Args:
            filename: Uploaded video filename used as a session-local dedupe key.
            outcome: Positive mock analysis outcome: fire or smoke.
            confidence: Deterministic mock confidence value.

        Returns:
            True if a new incident was created; otherwise False.
        """
        dedupe_key = filename.casefold()
        if dedupe_key in self._analyzed_video_names:
            return False

        event_type = (
            EventType.FIRE
            if outcome is VideoAnalysisOutcome.FIRE
            else EventType.SMOKE
        )
        event_number = len(self._provider.list_events()) + len(self._video_events) + 1
        event = DetectionEvent(
            id=f"VID-{event_number:03d}",
            event_type=event_type,
            camera_id="VIDEO-TEST",
            camera_name=f"Video Test: {filename}",
            confidence=confidence,
            detected_at=datetime.now(timezone.utc),
            severity=(
                Severity.CRITICAL
                if event_type is EventType.FIRE
                else Severity.HIGH
            ),
            status="New — mock video analysis",
        )
        self._video_events.insert(0, event)
        self._analyzed_video_names.add(dedupe_key)
        return True

    def get_metrics(self) -> DashboardMetrics:
        """Calculate dashboard counters from provider and video test data."""
        cameras = self._provider.list_cameras()
        events = self.list_events()
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
