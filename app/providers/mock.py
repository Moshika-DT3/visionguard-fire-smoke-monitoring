"""Deterministic sample data provider used by the standalone VisionGuard baseline."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence

from app.models import (
    CameraSource,
    CameraStatus,
    DetectionEvent,
    EventType,
    ProviderStatus,
    Severity,
)


class MockDetectionProvider:
    """Provide stable in-memory camera and detection records for demos."""

    def __init__(self) -> None:
        """Initialize the fixed sample records used in every application run."""
        self._cameras = (
            CameraSource(
                id="CAM-001",
                name="Main Entrance",
                location="Building A — Main Entrance",
                status=CameraStatus.ACTIVE,
                source_type="sample_rtsp",
            ),
            CameraSource(
                id="CAM-002",
                name="Warehouse North",
                location="Warehouse — North Aisle",
                status=CameraStatus.ACTIVE,
                source_type="sample_rtsp",
            ),
            CameraSource(
                id="CAM-003",
                name="Loading Bay",
                location="Building B — Loading Bay",
                status=CameraStatus.OFFLINE,
                source_type="sample_rtsp",
            ),
            CameraSource(
                id="CAM-004",
                name="Server Room",
                location="Building A — Level 2",
                status=CameraStatus.ACTIVE,
                source_type="sample_rtsp",
            ),
        )
        self._events = (
            DetectionEvent(
                id="EVT-2026-001",
                event_type=EventType.FIRE,
                camera_id="CAM-002",
                camera_name="Warehouse North",
                confidence=0.97,
                detected_at=datetime(2026, 9, 22, 10, 42, tzinfo=timezone.utc),
                severity=Severity.CRITICAL,
                status="Escalated",
            ),
            DetectionEvent(
                id="EVT-2026-002",
                event_type=EventType.SMOKE,
                camera_id="CAM-001",
                camera_name="Main Entrance",
                confidence=0.88,
                detected_at=datetime(2026, 9, 22, 9, 18, tzinfo=timezone.utc),
                severity=Severity.HIGH,
                status="Acknowledged",
            ),
            DetectionEvent(
                id="EVT-2026-003",
                event_type=EventType.SMOKE,
                camera_id="CAM-004",
                camera_name="Server Room",
                confidence=0.79,
                detected_at=datetime(2026, 9, 21, 18, 5, tzinfo=timezone.utc),
                severity=Severity.MEDIUM,
                status="Under review",
            ),
            DetectionEvent(
                id="EVT-2026-004",
                event_type=EventType.FIRE,
                camera_id="CAM-002",
                camera_name="Warehouse North",
                confidence=0.91,
                detected_at=datetime(2026, 9, 20, 14, 36, tzinfo=timezone.utc),
                severity=Severity.HIGH,
                status="Resolved",
            ),
            DetectionEvent(
                id="EVT-2026-005",
                event_type=EventType.SMOKE,
                camera_id="CAM-001",
                camera_name="Main Entrance",
                confidence=0.72,
                detected_at=datetime(2026, 9, 19, 11, 10, tzinfo=timezone.utc),
                severity=Severity.LOW,
                status="Resolved",
            ),
        )

    def list_cameras(self) -> Sequence[CameraSource]:
        """Return the deterministic camera inventory."""
        return self._cameras

    def list_events(self) -> Sequence[DetectionEvent]:
        """Return deterministic events ordered newest first."""
        return self._events

    def get_provider_status(self) -> ProviderStatus:
        """Return the baseline mock provider operational state."""
        return ProviderStatus(
            name="Mock Detection Provider",
            status="Operational",
            processing_status="Ready — deterministic sample stream",
        )
