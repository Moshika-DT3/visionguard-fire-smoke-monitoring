"""Provider contract for obtaining camera, event, and processing information."""

from __future__ import annotations

from typing import Protocol, Sequence

from app.models import CameraSource, DetectionEvent, ProviderStatus


class DetectionProvider(Protocol):
    """Read-only contract implemented by present and future detection integrations."""

    def list_cameras(self) -> Sequence[CameraSource]:
        """Return the configured monitoring sources in a stable display order."""

    def list_events(self) -> Sequence[DetectionEvent]:
        """Return detection events in a stable display order."""

    def get_provider_status(self) -> ProviderStatus:
        """Return the provider's current operational and processing state."""
