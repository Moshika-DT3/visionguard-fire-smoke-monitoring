"""Replaceable deterministic video-analysis adapter for the Video Testing flow."""

from __future__ import annotations

from pathlib import Path

from app.models import VideoAnalysisOutcome


class MockVideoAnalysisAdapter:
    """Map demo video filenames to deterministic workflow-validation outcomes.

    This adapter intentionally does not inspect video bytes, frames, metadata, or
    pixels. A future VisionAI adapter can implement the same ``analyze`` method
    while the upload routes and monitoring event integration remain unchanged.
    """

    provider_name = "Mock Video Analysis"

    def analyze(self, filename: str) -> tuple[VideoAnalysisOutcome, float | None]:
        """Return a deterministic outcome based only on the uploaded filename."""
        normalized_name = Path(filename).stem.casefold()

        if "fire_test" in normalized_name:
            return VideoAnalysisOutcome.FIRE, 0.96
        if "smoke_vd" in normalized_name:
            return VideoAnalysisOutcome.SMOKE, 0.89
        return VideoAnalysisOutcome.NO_DETECTION, None
