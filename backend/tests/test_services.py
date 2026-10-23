"""Unit regression tests for VisionGuard's existing deterministic mock services."""

import pytest

from backend.models import EventType, Severity, VideoAnalysisOutcome
from backend.providers.mock import MockDetectionProvider
from backend.services.monitoring import MonitoringService
from backend.services.video_analysis import MockVideoAnalysisAdapter


# PUBLIC_INTERFACE
@pytest.mark.parametrize(
    "filename,outcome,confidence",
    [
        ("fire_test.mp4", VideoAnalysisOutcome.FIRE, 0.96),
        ("FIRE_TEST.MP4", VideoAnalysisOutcome.FIRE, 0.96),
        ("prefix_fire_test_suffix.mp4", VideoAnalysisOutcome.FIRE, 0.96),
        ("smoke_vd.mp4", VideoAnalysisOutcome.SMOKE, 0.89),
        ("SMOKE_VD.MP4", VideoAnalysisOutcome.SMOKE, 0.89),
        ("prefix_smoke_vd_suffix.mp4", VideoAnalysisOutcome.SMOKE, 0.89),
        ("fire_test_smoke_vd.mp4", VideoAnalysisOutcome.FIRE, 0.96),
        ("ordinary.mp4", VideoAnalysisOutcome.NO_DETECTION, None),
        ("fire.mp4", VideoAnalysisOutcome.NO_DETECTION, None),
        ("smoke.mp4", VideoAnalysisOutcome.NO_DETECTION, None),
        ("", VideoAnalysisOutcome.NO_DETECTION, None),
    ],
)
def test_mock_filename_rules_are_repeatable(filename, outcome, confidence):
    """Check exact tokens, case folding, substring matches and fire priority."""
    adapter = MockVideoAnalysisAdapter()
    assert adapter.provider_name == "Mock Video Analysis"
    assert adapter.analyze(filename) == (outcome, confidence)
    assert adapter.analyze(filename) == adapter.analyze(filename)


# PUBLIC_INTERFACE
def test_baseline_metrics_and_status():
    """Validate the current baseline counters and provider health contract."""
    service = MonitoringService(MockDetectionProvider())
    assert service.get_metrics().model_dump() == {
        "active_cameras": 3,
        "total_incidents": 5,
        "fire_alerts": 2,
        "smoke_alerts": 3,
    }
    status = service.get_system_status()
    assert status.application_status == "Operational"
    assert status.active_sources == 3
    assert status.total_sources == 4
    assert status.provider.name == "Mock Detection Provider"
    assert status.provider.status == "Operational"
    assert status.provider.processing_status == "Ready — deterministic sample stream"


# PUBLIC_INTERFACE
@pytest.mark.parametrize(
    "filter_value,count,event_type",
    [
        ("all", 5, None),
        ("invalid", 5, None),
        ("fire", 2, EventType.FIRE),
        ("FIRE", 2, EventType.FIRE),
        ("smoke", 3, EventType.SMOKE),
    ],
)
def test_service_event_filters(filter_value, count, event_type):
    """Check service filtering independently of HTTP parameter normalization."""
    service = MonitoringService(MockDetectionProvider())
    events = service.list_events(filter_value)
    assert len(events) == count
    if event_type is not None:
        assert all(event.event_type is event_type for event in events)


# PUBLIC_INTERFACE
@pytest.mark.parametrize("limit", [0, 1, 4, 20])
def test_recent_event_limit(limit):
    """Verify recent events are the requested prefix of the stable history."""
    service = MonitoringService(MockDetectionProvider())
    assert service.get_recent_events(limit) == service.list_events()[:limit]


# PUBLIC_INTERFACE
@pytest.mark.parametrize(
    "filename,outcome,confidence,event_type,severity",
    [
        ("fire_test.mp4", VideoAnalysisOutcome.FIRE, 0.96, EventType.FIRE, Severity.CRITICAL),
        ("smoke_vd.mp4", VideoAnalysisOutcome.SMOKE, 0.89, EventType.SMOKE, Severity.HIGH),
    ],
)
def test_positive_incident_fields_and_dedupe(filename, outcome, confidence, event_type, severity):
    """Check positive incident construction and filename-case deduplication."""
    provider = MockDetectionProvider()
    service = MonitoringService(provider)
    baseline = tuple(service.list_events())
    assert service.create_video_incident(filename, outcome, confidence) is True
    incident = service.list_events()[0]
    assert incident.id == "VID-006"
    assert incident.event_type is event_type
    assert incident.severity is severity
    assert incident.camera_id == "VIDEO-TEST"
    assert incident.camera_name == f"Video Test: {filename}"
    assert incident.confidence == confidence
    assert incident.detected_at.utcoffset().total_seconds() == 0
    assert incident.status == "New — mock video analysis"
    assert tuple(service.list_events()[1:]) == baseline
    assert tuple(provider.list_events()) == baseline
    assert service.create_video_incident(filename.upper(), outcome, confidence) is False
    assert len(service.list_events()) == 6


# PUBLIC_INTERFACE
def test_dedupe_state_is_session_local():
    """Ensure separate service instances do not share generated incidents."""
    provider = MockDetectionProvider()
    first = MonitoringService(provider)
    second = MonitoringService(provider)
    assert first.create_video_incident(
        "fire_test.mp4", VideoAnalysisOutcome.FIRE, 0.96
    ) is True
    assert len(second.list_events()) == 5
    assert second.create_video_incident(
        "fire_test.mp4", VideoAnalysisOutcome.FIRE, 0.96
    ) is True
    assert len(first.list_events()) == len(second.list_events()) == 6
