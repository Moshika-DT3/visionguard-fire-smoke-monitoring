"""JSON API routes for deterministic VisionGuard monitoring data."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.models import (
    CameraSource,
    DetectionEvent,
    MonitoringStatus,
    VideoAnalysisOutcome,
    VideoAnalysisResult,
)
from app.services.monitoring import MonitoringService
from app.services.video_analysis import MockVideoAnalysisAdapter

ALLOWED_VIDEO_CONTENT_TYPES = {"video/mp4", "application/mp4"}


# PUBLIC_INTERFACE
def create_api_router(
    monitoring_service: MonitoringService,
    video_analysis_adapter: MockVideoAnalysisAdapter,
    upload_directory: Path,
) -> APIRouter:
    """Create JSON APIs for monitoring data and deterministic video testing.

    Args:
        monitoring_service: Service supplying monitoring views and event creation.
        video_analysis_adapter: Replaceable uploaded-video analysis component.
        upload_directory: Application-controlled directory for uploaded MP4 files.

    Returns:
        Router exposing existing monitoring APIs and Video Testing endpoints.
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

    @router.post(
        "/video-tests/upload",
        summary="Upload an MP4 video for testing",
        description=(
            "Stores a local demo MP4 for browser preview and deterministic mock "
            "workflow validation. Only MP4 uploads are accepted."
        ),
        responses={
            400: {"description": "No file or unsupported file type supplied."},
        },
    )
    async def upload_video(file: UploadFile = File(...)) -> dict[str, str]:
        """Store one MP4 upload and return its application-controlled identifier."""
        supplied_name = file.filename or ""
        is_mp4_extension = supplied_name.casefold().endswith(".mp4")
        is_accepted_type = (
            not file.content_type or file.content_type in ALLOWED_VIDEO_CONTENT_TYPES
        )
        if not supplied_name or not is_mp4_extension or not is_accepted_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please select a valid MP4 video file.",
            )

        upload_directory.mkdir(parents=True, exist_ok=True)
        stored_name = f"{uuid4().hex}.mp4"
        destination = upload_directory / stored_name
        content = await file.read()
        destination.write_bytes(content)

        return {
            "video_id": stored_name,
            "filename": Path(supplied_name).name,
            "preview_url": f"/api/video-tests/uploads/{stored_name}",
        }

    @router.get(
        "/video-tests/uploads/{video_id}",
        summary="Preview an uploaded test video",
        description="Streams a previously uploaded MP4 stored by the Video Testing flow.",
        responses={404: {"description": "Uploaded video was not found."}},
    )
    async def preview_video(video_id: str) -> FileResponse:
        """Serve an uploaded MP4 only when its safe stored identifier exists."""
        if Path(video_id).name != video_id or not video_id.endswith(".mp4"):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        video_path = upload_directory / video_id
        if not video_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Uploaded video was not found.",
            )
        return FileResponse(video_path, media_type="video/mp4")

    @router.post(
        "/video-tests/{video_id}/analyze",
        response_model=VideoAnalysisResult,
        summary="Run deterministic mock video analysis",
        description=(
            "Uses filename-only mock rules for workflow validation: fire_test "
            "maps to fire, smoke_vd maps to smoke, and all other filenames map "
            "to no detection. No pixels, frames, or ML models are evaluated."
        ),
        responses={404: {"description": "Uploaded video was not found."}},
    )
    async def analyze_video(video_id: str, filename: str) -> VideoAnalysisResult:
        """Analyze a saved MP4 and create a positive monitoring event once per name."""
        if Path(video_id).name != video_id or not video_id.endswith(".mp4"):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        if not (upload_directory / video_id).is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Uploaded video was not found.",
            )

        outcome, confidence = video_analysis_adapter.analyze(filename)
        incident_created = False
        if outcome is not VideoAnalysisOutcome.NO_DETECTION:
            incident_created = monitoring_service.create_video_incident(
                filename=filename,
                outcome=outcome,
                confidence=confidence or 0,
            )

        return VideoAnalysisResult(
            filename=filename,
            outcome=outcome,
            confidence=confidence,
            status="Completed successfully",
            provider=video_analysis_adapter.provider_name,
            incident_created=incident_created,
        )

    return router
