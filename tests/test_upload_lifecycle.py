"""Step 2 regressions for bounded uploads and local demo session cleanup."""

from io import BytesIO
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.datastructures import UploadFile

from app import main
from app.providers.mock import MockDetectionProvider
from app.routers import api
from app.services.monitoring import MonitoringService
from app.services.video_analysis import MockVideoAnalysisAdapter


def _router(directory, limit=8):
    """Compose real upload routes with a small, deterministic test limit."""
    return api.create_api_router(
        MonitoringService(MockDetectionProvider()),
        MockVideoAnalysisAdapter(),
        directory,
        max_upload_bytes=limit,
    )


def _application(directory, limit=8):
    """Return isolated HTTP composition without touching production uploads."""
    application = FastAPI()
    application.include_router(_router(directory, limit))
    return application


# PUBLIC_INTERFACE
@pytest.mark.parametrize("content,expected", [(b"", 400), (b"123456789", 413)])
def test_rejected_content_leaves_no_upload(tmp_path, content, expected):
    """Empty and oversized files leave neither output nor monitoring changes."""
    with TestClient(_application(tmp_path)) as client:
        before = client.get("/api/events").json()
        response = client.post(
            "/api/video-tests/upload",
            files={"file": ("fire_test.mp4", content, "video/mp4")},
        )
        assert response.status_code == expected
        assert list(tmp_path.iterdir()) == []
        assert client.get("/api/events").json() == before


# PUBLIC_INTERFACE
def test_exact_limit_and_repeated_uploads_remain_previewable(tmp_path):
    """The inclusive limit preserves separate uploads and mock incident dedupe."""
    with TestClient(_application(tmp_path)) as client:
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
        assert len(list(tmp_path.iterdir())) == 2


# PUBLIC_INTERFACE
def test_oversized_upload_does_not_remove_previous_upload(tmp_path):
    """Rejecting a replacement preserves the earlier successful preview."""
    with TestClient(_application(tmp_path)) as client:
        upload = client.post(
            "/api/video-tests/upload",
            files={"file": ("ordinary.mp4", b"original", "video/mp4")},
        ).json()
        response = client.post(
            "/api/video-tests/upload",
            files={"file": ("ordinary.mp4", b"too large", "video/mp4")},
        )
        assert response.status_code == 413
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
@pytest.mark.parametrize("limit", [0, -1])
def test_upload_limit_must_be_positive(tmp_path, limit):
    """Reject invalid server limits during composition, not during uploads."""
    with pytest.raises(ValueError, match="max_upload_bytes must be positive"):
        _router(tmp_path, limit)
