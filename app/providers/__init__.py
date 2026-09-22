"""Detection provider contracts and concrete provider implementations."""

from app.providers.base import DetectionProvider
from app.providers.mock import MockDetectionProvider

__all__ = ["DetectionProvider", "MockDetectionProvider"]
