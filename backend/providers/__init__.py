"""Detection provider contracts and concrete provider implementations."""

from backend.providers.base import DetectionProvider
from backend.providers.mock import MockDetectionProvider

__all__ = ["DetectionProvider", "MockDetectionProvider"]
