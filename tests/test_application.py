"""HTTP regression coverage for the current VisionGuard application.

Run from the repository root:
    .\\.venv\\Scripts\\python.exe -m pytest -q
Optional coverage:
    .\\.venv\\Scripts\\python.exe -m pytest --cov=app --cov-report=term-missing

Test dependencies: pytest, httpx (FastAPI TestClient), and optionally pytest-cov.
No application files are changed. The router factories accept a fresh service
and temporary uploads, but create_page_router reuses a module-level APIRouter.
Repeated calls accumulate handlers bound to earlier services. The fixture
monkeypatches that router with a fresh instance and restores it after each test.
A recommended application testability improvement is to instantiate APIRouter
inside create_page_router, as create_api_router already does; it is not required
for the current single-composition entry point and is not implemented here.
Tests use real templates, monitoring providers and routes, with a path-based
YOLO adapter test double instead of ML inference or video decoding.
Read-only smoke checks also verify the actual app.main:app composition.

Current boundaries (not new requirements): upload validation checks extension and
declared MIME type and rejects empty content, but imposes no file-size limit or
MP4 byte inspection. Analysis receives the saved upload path; the query filename
is display and incident-deduplication metadata only. Dedupe is per service
session and case-insensitive filename, not file content or upload ID. Browser
JavaScript execution and actual media playback require separate browser tests.
If those contracts change later, application changes and new tests are needed.
"""

from datetime import datetime, timezone
from pathlib import Path
import re
from unittest.mock import create_autospec

import pytest
from fastapi import APIRouter, FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient

from app.main import APP_DIRECTORY, app as production_app, templates
from app.models import VideoAnalysisOutcome
from app.providers.mock import MockDetectionProvider
from app.routers import pages
from app.routers.api import create_api_router
from app.routers.pages import create_page_router
from app.services.monitoring import MonitoringService
from app.services.video_analysis import YoloVideoAnalysisAdapter


# PUBLIC_INTERFACE
@pytest.fixture
def service():
    """Provide independent monitoring state for every HTTP test."""
    return MonitoringService(MockDetectionProvider())


# PUBLIC_INTERFACE
@pytest.fixture
def video_analysis_adapter():
    """Provide controlled inference results through the current adapter API."""
    adapter = create_autospec(YoloVideoAnalysisAdapter, instance=True)
    adapter.provider_name = YoloVideoAnalysisAdapter.provider_name
    adapter.analyze.return_value = (VideoAnalysisOutcome.NO_DETECTION, None)
    return adapter


# PUBLIC_INTERFACE
@pytest.fixture
def client(service, tmp_path, monkeypatch, video_analysis_adapter):
    """Exercise production routes with real templates and temporary uploads."""
    # The current page factory registers handlers on a shared module router.
    # Replacing it avoids stale service closures without changing application code.
    monkeypatch.setattr(pages, "router", APIRouter(tags=["Monitoring pages"]))
    application = FastAPI()
    application.mount(
        "/static",
        StaticFiles(directory=str(APP_DIRECTORY / "static")),
        name="static",
    )
    application.include_router(create_page_router(templates, service))
    application.include_router(
        create_api_router(service, video_analysis_adapter, tmp_path)
    )
    with TestClient(application) as test_client:
        yield test_client
    # Every analysis must use a saved upload, never the display/query filename.
    for analysis_call in video_analysis_adapter.analyze.call_args_list:
        (video_path,) = analysis_call.args
        assert isinstance(video_path, Path)
        assert video_path.parent == tmp_path
        assert video_path.is_file()


def _upload(client, filename="fire_test.mp4", content=b"mock video bytes"):
    """Upload synthetic bytes; inference is replaced by a test double."""
    response = client.post(
        "/api/video-tests/upload",
        files={"file": (filename, content, "video/mp4")},
    )
    assert response.status_code == 200, response.text
    return response.json()


def _analyze(client, upload, filename=None):
    """Analyze a saved upload with its display/deduplication filename."""
    response = client.post(
        f"/api/video-tests/{upload['video_id']}/analyze",
        params={"filename": filename or upload["filename"]},
    )
    assert response.status_code == 200, response.text
    return response.json()


# PUBLIC_INTERFACE
@pytest.mark.parametrize(
    "path,heading",
    [
        ("/", "VisionGuard"),
        ("/cameras", "Camera Sources"),
        ("/incidents", "Incident History"),
        ("/status", "System Status"),
        ("/video-testing", "Video Testing"),
    ],
)
def test_pages_render(client, path, heading):
    """Verify each current page renders HTML with its expected heading."""
    response = client.get(path)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert f"<h1>{heading}</h1>" in response.text


# PUBLIC_INTERFACE
def test_dashboard_metrics_and_recent_events(client):
    """Check rendered baseline counters and the four most recent incidents."""
    response = client.get("/")
    assert response.context["metrics"].model_dump() == {
        "active_cameras": 3,
        "total_incidents": 5,
        "fire_alerts": 2,
        "smoke_alerts": 3,
    }
    for label, count in [
        ("Active Cameras", 3),
        ("Total Incidents", 5),
        ("Fire Alerts", 2),
        ("Smoke Alerts", 3),
    ]:
        assert re.search(
            rf"{label}</span>\s*<strong>{count}</strong>", response.text
        )
    assert [
        event.id for event in response.context["recent_events"]
    ] == [f"EVT-2026-{number:03d}" for number in range(1, 5)]
    assert "EVT-2026-005" not in response.text
    assert "Mock Detection Provider" in response.text
    assert "3 of 4" in response.text


# PUBLIC_INTERFACE
def test_camera_sources_include_offline_inventory(client):
    """Check every source's identifier, name, location and availability."""
    response = client.get("/cameras")
    cameras = response.context["cameras"]
    assert len(cameras) == 4
    for camera in cameras:
        assert camera.id in response.text
        assert camera.name in response.text
        assert camera.location in response.text
        assert camera.source_type in response.text
    assert 'class="source-status offline"' in response.text
    assert sum(camera.status.value == "active" for camera in cameras) == 3


# PUBLIC_INTERFACE
@pytest.mark.parametrize(
    "filter_value,selected,indices",
    [
        ("all", "all", [1, 2, 3, 4, 5]),
        ("fire", "fire", [1, 4]),
        ("smoke", "smoke", [2, 3, 5]),
        ("FIRE", "fire", [1, 4]),
        ("invalid", "all", [1, 2, 3, 4, 5]),
    ],
)
def test_incident_history_filters(client, filter_value, selected, indices):
    """Verify normalized filters and rendered inclusion/exclusion of events."""
    response = client.get("/incidents", params={"type": filter_value})
    assert response.status_code == 200
    assert response.context["selected_type"] == selected
    assert [event.id for event in response.context["events"]] == [
        f"EVT-2026-{number:03d}" for number in indices
    ]
    for number in range(1, 6):
        assert (f"EVT-2026-{number:03d}" in response.text) == (number in indices)


# PUBLIC_INTERFACE
def test_system_status_page(client):
    """Check operational provider state and active-source totals."""
    response = client.get("/status")
    for text in [
        "Operational",
        "Mock Detection Provider",
        "Ready — deterministic sample stream",
        "3 / 4",
    ]:
        assert text in response.text


# PUBLIC_INTERFACE
def test_video_testing_page_controls_and_script(client):
    """Verify upload, preview and analysis UI hooks and script reachability."""
    response = client.get("/video-testing")
    for element_id in [
        "video-upload-form",
        "video-file",
        "video-preview",
        "analyze-button",
        "analysis-result",
        "result-outcome",
        "result-confidence",
        "result-incident",
    ]:
        assert f'id="{element_id}"' in response.text
    assert 'accept="video/mp4,.mp4"' in response.text
    assert "YOLO Video Analysis" in response.text
    assert "/static/js/video_testing.js" in response.text
    assert client.get("/static/js/video_testing.js").status_code == 200


# PUBLIC_INTERFACE
def test_health_api(client):
    """Verify the complete deterministic health response."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {
        "application_status": "Operational",
        "provider": {
            "name": "Mock Detection Provider",
            "status": "Operational",
            "processing_status": "Ready — deterministic sample stream",
        },
        "active_sources": 3,
        "total_sources": 4,
    }


# PUBLIC_INTERFACE
def test_cameras_api(client, service):
    """Verify JSON camera serialization and ordering."""
    response = client.get("/api/cameras")
    assert response.status_code == 200
    assert response.json() == [
        camera.model_dump(mode="json") for camera in service.list_cameras()
    ]
    assert [camera["id"] for camera in response.json()] == [
        "CAM-001", "CAM-002", "CAM-003", "CAM-004"
    ]
    assert response.json()[2]["status"] == "offline"


# PUBLIC_INTERFACE
def test_events_api(client, service):
    """Verify event fields, JSON serialization and newest-first ordering."""
    response = client.get("/api/events")
    assert response.status_code == 200
    events = response.json()
    assert events == [
        event.model_dump(mode="json") for event in service.list_events()
    ]
    assert len(events) == 5
    assert [event["event_type"] for event in events] == [
        "fire", "smoke", "smoke", "fire", "smoke"
    ]
    timestamps = [datetime.fromisoformat(event["detected_at"]) for event in events]
    assert timestamps == sorted(timestamps, reverse=True)


# PUBLIC_INTERFACE
@pytest.mark.parametrize(
    "filename,mime",
    [
        ("fire_test.mp4", "video/mp4"),
        ("SMOKE_VD.MP4", "application/mp4"),
    ],
)
def test_mp4_upload_and_preview(client, tmp_path, filename, mime):
    """Verify accepted MP4 types, generated storage names and preview bytes."""
    content = b"synthetic MP4 upload; no decoding expected"
    response = client.post(
        "/api/video-tests/upload", files={"file": (filename, content, mime)}
    )
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {"video_id", "filename", "preview_url"}
    assert re.fullmatch(r"[0-9a-f]{32}\.mp4", data["video_id"])
    assert data["filename"] == filename
    assert data["preview_url"] == f"/api/video-tests/uploads/{data['video_id']}"
    assert (tmp_path / data["video_id"]).read_bytes() == content
    preview = client.get(data["preview_url"])
    assert preview.status_code == 200
    assert preview.headers["content-type"] == "video/mp4"
    assert preview.content == content


# PUBLIC_INTERFACE
def test_167_mib_no_fire_upload_preview_and_analysis(client, service, tmp_path):
    """Accept a 167 MiB multipart file and preserve No Detection monitoring state.

    Synthetic bytes exercise the size contract, not browser media decoding.
    167 MiB also exceeds the reported 167 MB when MB uses decimal units.
    """
    size = 167 * 1024 * 1024
    source = tmp_path / "no fire.mp4"
    # A sparse fixture avoids allocating the full video in a Python bytes object.
    with source.open("wb") as handle:
        handle.write(b"synthetic video fixture")
        handle.truncate(size)

    before_events = client.get("/api/events").json()
    before_metrics = service.get_metrics().model_dump()
    before_dashboard = client.get("/").text
    before_history = client.get("/incidents").text
    with source.open("rb") as handle:
        response = client.post(
            "/api/video-tests/upload",
            files={"file": (source.name, handle, "video/mp4")},
        )
    assert response.status_code == 200, response.text
    upload = response.json()
    assert upload["filename"] == "no fire.mp4"
    assert (tmp_path / upload["video_id"]).stat().st_size == size
    assert client.get("/api/events").json() == before_events

    # Fetch a bounded preview range while checking the total uploaded size.
    preview = client.get(upload["preview_url"], headers={"Range": "bytes=0-31"})
    assert preview.status_code == 206
    assert preview.headers["content-type"] == "video/mp4"
    assert preview.headers["content-range"] == f"bytes 0-31/{size}"
    with source.open("rb") as handle:
        assert preview.content == handle.read(32)

    result = _analyze(client, upload)
    assert result == {
        "filename": "no fire.mp4",
        "outcome": "no_detection",
        "confidence": None,
        "status": "Completed successfully",
        "provider": "YOLO Video Analysis",
        "incident_created": False,
    }
    assert client.get("/api/events").json() == before_events
    assert service.get_metrics().model_dump() == before_metrics
    assert client.get("/").text == before_dashboard
    assert client.get("/incidents").text == before_history


# PUBLIC_INTERFACE
@pytest.mark.parametrize(
    "filename,mime",
    [
        ("video.avi", "video/mp4"),
        ("video.mp4.exe", "video/mp4"),
        ("video", "video/mp4"),
        ("video.mp4", "text/plain"),
        ("video.mp4", "application/octet-stream"),
    ],
)
def test_invalid_upload_rejected_without_side_effects(client, tmp_path, filename, mime):
    """Reject unsupported extensions or MIME types without writes or incidents."""
    before = client.get("/api/events").json()
    response = client.post(
        "/api/video-tests/upload", files={"file": (filename, b"bytes", mime)}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Please select a valid MP4 video file."}
    assert list(tmp_path.iterdir()) == []
    assert client.get("/api/events").json() == before


# PUBLIC_INTERFACE
def test_missing_upload_file_is_validation_error(client, tmp_path):
    """Verify FastAPI rejects absent multipart file input without writing."""
    response = client.post("/api/video-tests/upload")
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "file"]
    assert list(tmp_path.iterdir()) == []


# PUBLIC_INTERFACE
def test_repeated_upload_uses_distinct_storage_names(client, tmp_path):
    """Ensure repeated filenames do not overwrite prior stored content."""
    first = _upload(client, content=b"first")
    second = _upload(client, content=b"second")
    assert first["video_id"] != second["video_id"]
    assert (tmp_path / first["video_id"]).read_bytes() == b"first"
    assert (tmp_path / second["video_id"]).read_bytes() == b"second"


# PUBLIC_INTERFACE
@pytest.mark.parametrize("video_id", ["missing.mp4", "missing.txt", "missing.MP4"])
@pytest.mark.parametrize("operation", ["preview", "analyze"])
def test_missing_or_invalid_video_id(client, video_id, operation):
    """Verify invalid or absent stored IDs return 404 and do not create events."""
    before = client.get("/api/events").json()
    if operation == "preview":
        response = client.get(f"/api/video-tests/uploads/{video_id}")
    else:
        response = client.post(
            f"/api/video-tests/{video_id}/analyze",
            params={"filename": "fire_test.mp4"},
        )
    assert response.status_code == 404
    assert client.get("/api/events").json() == before


# PUBLIC_INTERFACE
def test_analysis_requires_filename(client):
    """Verify filename query validation leaves monitoring state unchanged."""
    upload = _upload(client)
    response = client.post(f"/api/video-tests/{upload['video_id']}/analyze")
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", "filename"]
    assert len(client.get("/api/events").json()) == 5


# PUBLIC_INTERFACE
@pytest.mark.parametrize(
    "filename,outcome,confidence,severity",
    [
        ("fire_test.mp4", "fire", 0.96, "critical"),
        ("smoke_vd.mp4", "smoke", 0.89, "high"),
        ("ordinary.mp4", "no_detection", None, None),
    ],
)
def test_analysis_incident_flow(
    client, service, video_analysis_adapter, tmp_path,
    filename, outcome, confidence, severity,
):
    """Check controlled path-based results and monitoring side effects."""
    video_analysis_adapter.analyze.return_value = (
        VideoAnalysisOutcome(outcome), confidence
    )
    before = client.get("/api/events").json()
    upload = _upload(client, filename)
    # Upload alone must not create an incident.
    assert client.get("/api/events").json() == before
    started_at = datetime.now(timezone.utc)
    result = _analyze(client, upload)
    finished_at = datetime.now(timezone.utc)
    video_analysis_adapter.analyze.assert_called_once_with(
        tmp_path / upload["video_id"]
    )
    positive = outcome != "no_detection"
    assert result == {
        "filename": filename,
        "outcome": outcome,
        "confidence": confidence,
        "status": "Completed successfully",
        "provider": "YOLO Video Analysis",
        "incident_created": positive,
    }
    events = client.get("/api/events").json()
    metrics = service.get_metrics()
    assert metrics.total_incidents == 5 + int(positive)
    assert metrics.fire_alerts == 2 + int(outcome == "fire")
    assert metrics.smoke_alerts == 3 + int(outcome == "smoke")
    assert metrics.active_cameras == 3
    if not positive:
        assert events == before
        assert _analyze(client, upload)["incident_created"] is False
        assert client.get("/api/events").json() == before
        return
    assert events[1:] == before
    incident = events[0]
    assert incident["id"] == "VID-006"
    assert incident["event_type"] == outcome
    assert incident["camera_id"] == "VIDEO-TEST"
    assert incident["camera_name"] == f"Video Test: {filename}"
    assert incident["confidence"] == confidence
    assert incident["severity"] == severity
    assert incident["status"] == "New — mock video analysis"
    assert started_at <= datetime.fromisoformat(incident["detected_at"]) <= finished_at
    assert "VID-006" in client.get("/").text
    assert "VID-006" in client.get("/incidents", params={"type": outcome}).text
    opposite = "smoke" if outcome == "fire" else "fire"
    assert "VID-006" not in client.get("/incidents", params={"type": opposite}).text


# PUBLIC_INTERFACE
@pytest.mark.parametrize(
    "filename,outcome,confidence",
    [
        ("fire_test.mp4", VideoAnalysisOutcome.FIRE, 0.96),
        ("smoke_vd.mp4", VideoAnalysisOutcome.SMOKE, 0.89),
    ],
)
def test_duplicate_incident_prevention_across_uploads(
    client, video_analysis_adapter, filename, outcome, confidence,
):
    """Check repeat analysis, case variants and reuploads share a dedupe key."""
    video_analysis_adapter.analyze.return_value = (outcome, confidence)
    first = _upload(client, filename)
    assert _analyze(client, first)["incident_created"] is True
    expected_events = client.get("/api/events").json()
    assert _analyze(client, first)["incident_created"] is False
    second = _upload(client, filename.upper())
    assert _analyze(client, second)["incident_created"] is False
    assert client.get("/api/events").json() == expected_events
    assert len(expected_events) == 6


# PUBLIC_INTERFACE
def test_distinct_positive_filenames_create_unique_incidents(
    client, video_analysis_adapter,
):
    """Check distinct filenames create unique newest-first generated incidents."""
    for filename, outcome, confidence in [
        ("fire_test.mp4", VideoAnalysisOutcome.FIRE, 0.96),
        ("smoke_vd.mp4", VideoAnalysisOutcome.SMOKE, 0.89),
        ("another_fire_test.mp4", VideoAnalysisOutcome.FIRE, 0.96),
    ]:
        video_analysis_adapter.analyze.return_value = (outcome, confidence)
        assert _analyze(client, _upload(client, filename))["incident_created"] is True
    events = client.get("/api/events").json()
    assert [event["id"] for event in events[:3]] == [
        "VID-008", "VID-007", "VID-006"
    ]
    assert len({event["id"] for event in events}) == 8


# PUBLIC_INTERFACE
@pytest.mark.parametrize(
    "path",
    [
        "/", "/cameras", "/incidents", "/status", "/video-testing",
        "/api/health", "/api/cameras", "/api/events",
        "/static/js/video_testing.js",
    ],
)
def test_production_entry_point_exposes_routes(path):
    """Smoke-test actual main application wiring without modifying its state."""
    with TestClient(production_app) as client:
        assert client.get(path).status_code == 200
