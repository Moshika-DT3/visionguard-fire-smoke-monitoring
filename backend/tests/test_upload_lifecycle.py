"""Regressions for chunked, size-unrestricted uploads and demo session cleanup."""

from io import BytesIO
from pathlib import Path
from unittest.mock import call, create_autospec

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.datastructures import UploadFile

from backend import main
from backend.models import VideoAnalysisOutcome
from backend.providers.mock import MockDetectionProvider
from backend.routers import api
from backend.services.monitoring import MonitoringService
from backend.services.video_analysis import YoloVideoAnalysisAdapter


def _router(directory, video_analysis_adapter=None):
    """Compose real upload routes without an application file-size limit."""
    return api.create_api_router(
        MonitoringService(MockDetectionProvider()),
        video_analysis_adapter if video_analysis_adapter is not None
        else YoloVideoAnalysisAdapter(),
        directory,
    )


def _application(directory, video_analysis_adapter=None):
    """Return isolated HTTP composition without touching production uploads."""
    application = FastAPI()
    application.include_router(_router(directory, video_analysis_adapter))
    return application


# PUBLIC_INTERFACE
def test_empty_content_leaves_no_upload(tmp_path):
    """Empty files leave neither output nor monitoring changes."""
    with TestClient(_application(tmp_path)) as client:
        before = client.get("/api/events").json()
        response = client.post(
            "/api/video-tests/upload",
            files={"file": ("fire_test.mp4", b"", "video/mp4")},
        )
        assert response.status_code == 400
        assert list(tmp_path.iterdir()) == []
        assert client.get("/api/events").json() == before


# PUBLIC_INTERFACE
def test_repeated_uploads_remain_previewable(tmp_path):
    """Separate upload paths remain previewable and preserve incident dedupe."""
    adapter = create_autospec(YoloVideoAnalysisAdapter, instance=True)
    adapter.provider_name = YoloVideoAnalysisAdapter.provider_name
    adapter.analyze.return_value = (VideoAnalysisOutcome.FIRE, 0.96)
    with TestClient(_application(tmp_path, adapter)) as client:
        uploads = []
        for content in (b"12345678", b"abcdefgh"):
            response = client.post(
                "/api/video-tests/upload",
                files={"file": ("fire_test.mp4", content, "video/mp4")},
            )
            assert response.status_code == 200
            upload = response.json()
            uploads.append(upload)
            assert client.get(upload["preview_url"]).content == content
        assert uploads[0]["video_id"] != uploads[1]["video_id"]
        for index, upload in enumerate(uploads):
            response = client.post(
                f"/api/video-tests/{upload['video_id']}/analyze",
                params={"filename": upload["filename"]},
            )
            assert response.status_code == 200
            assert response.json()["outcome"] == "fire"
            assert response.json()["incident_created"] is (index == 0)
        assert adapter.analyze.call_args_list == [
            call(tmp_path / upload["video_id"]) for upload in uploads
        ]
        assert len(list(tmp_path.iterdir())) == 2


# PUBLIC_INTERFACE
def test_invalid_upload_does_not_remove_previous_upload(tmp_path):
    """Rejecting a non-MP4 replacement preserves the earlier preview."""
    with TestClient(_application(tmp_path)) as client:
        upload = client.post(
            "/api/video-tests/upload",
            files={"file": ("ordinary.mp4", b"original", "video/mp4")},
        ).json()
        response = client.post(
            "/api/video-tests/upload",
            files={"file": ("ordinary.avi", b"replacement", "video/mp4")},
        )
        assert response.status_code == 400
        assert client.get(upload["preview_url"]).content == b"original"
        assert len(list(tmp_path.iterdir())) == 1


# PUBLIC_INTERFACE
def test_storage_error_returns_controlled_response(tmp_path, monkeypatch):
    """An output write failure deletes the partial file and leaves no incident."""
    original_open = Path.open

    class FailingOutput:
        """Simulate a local disk write failure after exclusive creation."""

        def __init__(self, handle):
            self.handle = handle

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.handle.close()

        def write(self, chunk):
            self.handle.write(chunk[:1])
            raise OSError("simulated disk write failure")

    def failing_open(path, mode="r", *args, **kwargs):
        handle = original_open(path, mode, *args, **kwargs)
        return FailingOutput(handle) if mode == "xb" else handle

    monkeypatch.setattr(Path, "open", failing_open)
    with TestClient(_application(tmp_path)) as client:
        response = client.post(
            "/api/video-tests/upload",
            files={"file": ("fire_test.mp4", b"123", "video/mp4")},
        )
        assert response.status_code == 500
        assert response.json() == {
            "detail": "The video could not be saved to local storage."
        }
        assert list(tmp_path.iterdir()) == []
        assert len(client.get("/api/events").json()) == 5


# PUBLIC_INTERFACE
@pytest.mark.parametrize("invalid", [False, True])
def test_upload_reads_bounded_chunks_and_closes_handle(tmp_path, monkeypatch, invalid):
    """The route closes upload handles even when extension validation rejects."""
    import asyncio

    class RecordingUpload(UploadFile):
        """Record requested read sizes without relying on multipart internals."""

        async def read(self, size=-1):
            self.read_sizes.append(size)
            return await super().read(size)

    monkeypatch.setattr(api, "UPLOAD_CHUNK_BYTES", 3)
    upload = RecordingUpload(
        file=BytesIO(b"12345678"),
        filename="video.txt" if invalid else "video.mp4",
    )
    upload.read_sizes = []
    endpoint = next(
        route.endpoint for route in _router(tmp_path).routes
        if route.path == "/api/video-tests/upload"
    )
    if invalid:
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as error:
            asyncio.run(endpoint(upload))
        assert error.value.status_code == 400
        assert upload.read_sizes == []
    else:
        result = asyncio.run(endpoint(upload))
        assert (tmp_path / result["video_id"]).read_bytes() == b"12345678"
        assert upload.read_sizes == [3, 3, 3, 3]
    assert upload.file.closed


# PUBLIC_INTERFACE
def test_session_cleanup_removes_generated_files_only(tmp_path, monkeypatch):
    """Startup handles stale uploads; shutdown cleans this session, not other files."""
    monkeypatch.setattr(main, "UPLOAD_DIRECTORY", tmp_path)
    stale = tmp_path / ("a" * 32 + ".mp4")
    current = tmp_path / ("b" * 32 + ".mp4")
    unrelated = tmp_path / "demo.mp4"
    other_suffix = tmp_path / ("c" * 32 + ".txt")
    stale.write_bytes(b"stale")
    unrelated.write_bytes(b"keep")
    other_suffix.write_bytes(b"keep")
    with TestClient(FastAPI(lifespan=main.lifespan)):
        assert not stale.exists()
        assert unrelated.exists()
        current.write_bytes(b"current")
        assert current.exists()
    assert not current.exists()
    assert unrelated.read_bytes() == b"keep"
    assert other_suffix.read_bytes() == b"keep"


# PUBLIC_INTERFACE
def test_cleanup_with_absent_upload_directory(tmp_path, monkeypatch):
    """Starting without any uploads must not create or require the directory."""
    missing = tmp_path / "not-created"
    monkeypatch.setattr(main, "UPLOAD_DIRECTORY", missing)
    with TestClient(FastAPI(lifespan=main.lifespan)):
        assert not missing.exists()
    assert not missing.exists()


# PUBLIC_INTERFACE
def test_upload_schema_has_no_size_rejection(tmp_path):
    """OpenAPI retains type/storage errors without advertising a size cap."""
    operation = _application(tmp_path).openapi()["paths"]["/api/video-tests/upload"]["post"]
    assert "413" not in operation["responses"]
    assert "400" in operation["responses"]
    assert "500" in operation["responses"]
    assert "without an application-level file-size limit" in operation["description"]
