"""Domain models shared by VisionGuard providers, services, routes, and templates."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class CameraStatus(str, Enum):
    """Operational state for a configured monitoring source."""

    ACTIVE = "active"
    OFFLINE = "offline"


class EventType(str, Enum):
    """Supported hazardous detection categories."""

    FIRE = "fire"
    SMOKE = "smoke"


class Severity(str, Enum):
    """Visual urgency levels assigned to detection events."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CameraSource(BaseModel):
    """A camera or video source available to the monitoring application."""

    id: str = Field(..., description="Stable camera source identifier.")
    name: str = Field(..., description="Human-readable source name.")
    location: str = Field(..., description="Physical or logical monitoring location.")
    status: CameraStatus = Field(..., description="Current source availability.")
    source_type: str = Field(
        ...,
        description="Source technology label, retained for future RTSP integration.",
    )


class DetectionEvent(BaseModel):
    """A single fire or smoke detection emitted by a detection provider."""

    id: str = Field(..., description="Stable detection event identifier.")
    event_type: EventType = Field(..., description="Detected hazard category.")
    camera_id: str = Field(..., description="Identifier of the emitting camera source.")
    camera_name: str = Field(..., description="Display name of the emitting camera.")
    confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Provider confidence from zero to one.",
    )
    detected_at: datetime = Field(..., description="Fixed ISO-8601 detection timestamp.")
    severity: Severity = Field(..., description="Operational severity classification.")
    status: str = Field(..., description="Current incident handling status.")


class ProviderStatus(BaseModel):
    """Health and processing state advertised by a detection provider."""

    name: str = Field(..., description="Display name of the active provider.")
    status: str = Field(..., description="Provider availability state.")
    processing_status: str = Field(..., description="Provider processing state.")


class MonitoringStatus(BaseModel):
    """Aggregated system status rendered by dashboard and API consumers."""

    application_status: str = Field(..., description="VisionGuard application state.")
    provider: ProviderStatus = Field(..., description="Current detection provider state.")
    active_sources: int = Field(..., description="Number of active camera sources.")
    total_sources: int = Field(..., description="Number of configured camera sources.")


class DashboardMetrics(BaseModel):
    """Deterministic incident counts shown in the dashboard summary."""

    active_cameras: int = Field(..., description="Number of active camera sources.")
    total_incidents: int = Field(..., description="Number of known detection events.")
    fire_alerts: int = Field(..., description="Number of fire detection events.")
    smoke_alerts: int = Field(..., description="Number of smoke detection events.")


class VideoAnalysisOutcome(str, Enum):
    """Supported deterministic outcomes for uploaded demo videos."""

    FIRE = "fire"
    SMOKE = "smoke"
    NO_DETECTION = "no_detection"


class VideoAnalysisResult(BaseModel):
    """Result produced by a replaceable uploaded-video analysis adapter."""

    filename: str = Field(..., description="Original uploaded MP4 filename.")
    outcome: VideoAnalysisOutcome = Field(
        ...,
        description="Deterministic mock hazard outcome for the uploaded video.",
    )
    confidence: float | None = Field(
        default=None,
        ge=0,
        le=1,
        description="Mock confidence for positive detections only.",
    )
    status: str = Field(..., description="Completion state of the analysis request.")
    provider: str = Field(..., description="Name of the video analysis adapter.")
    incident_created: bool = Field(
        ...,
        description="Whether this result created a new monitoring incident.",
    )
