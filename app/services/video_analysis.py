"""Replaceable adapters for deterministic and YOLO-backed video analysis."""

from __future__ import annotations

from pathlib import Path
from threading import Lock
from typing import Any, ClassVar, Mapping, Sequence

from app.models import VideoAnalysisOutcome


class VideoAnalysisInferenceError(RuntimeError):
    """Raised when a video cannot be analyzed by the YOLO adapter."""


class MockVideoAnalysisAdapter:
    """Map demo video filenames to deterministic workflow-validation outcomes.

    This adapter intentionally does not inspect video bytes, frames, metadata, or
    pixels. A future VisionAI adapter can implement the same ``analyze`` method
    while the upload routes and monitoring event integration remain unchanged.
    """

    provider_name = "Mock Video Analysis"

    # PUBLIC_INTERFACE
    def analyze(self, filename: str) -> tuple[VideoAnalysisOutcome, float | None]:
        """Return a deterministic outcome based only on the uploaded filename."""
        normalized_name = Path(filename).stem.casefold()

        if "fire_test" in normalized_name:
            return VideoAnalysisOutcome.FIRE, 0.96
        if "smoke_vd" in normalized_name:
            return VideoAnalysisOutcome.SMOKE, 0.89
        return VideoAnalysisOutcome.NO_DETECTION, None


class YoloVideoAnalysisAdapter:
    """Analyze uploaded video frames using the configured Ultralytics YOLO model.

    Models are loaded only when an analysis is requested and cached per checkpoint
    path for the process lifetime. This keeps application startup independent of
    the YOLO runtime while avoiding repeated checkpoint loading.
    """

    provider_name = "YOLO Video Analysis"
    default_model_path = Path(r"E:\Downloads\fire_smoke_yolov8n.pt")
    _model_cache: ClassVar[dict[Path, Any]] = {}
    _model_cache_lock: ClassVar[Lock] = Lock()

    def __init__(self, model_path: str | Path = default_model_path) -> None:
        """Configure the checkpoint that will be lazily loaded for inference."""
        self._model_path = Path(model_path)

    # PUBLIC_INTERFACE
    def analyze(
        self, video_path: str | Path
    ) -> tuple[VideoAnalysisOutcome, float | None]:
        """Analyze an uploaded video and return its accepted hazard outcome.

        Fire detections with confidence of at least 0.50 and smoke detections
        with confidence of at least 0.50 must occur in three and one distinct
        prediction frames, respectively, before being accepted. Fire takes
        precedence if both outcomes qualify. Positive results return their
        greatest supporting confidence; no detection returns ``None``.

        Args:
            video_path: Verified filesystem path to the uploaded video.

        Returns:
            The accepted hazard outcome and its confidence, if any.

        Raises:
            VideoAnalysisInferenceError: If the checkpoint or video cannot be
                processed by Ultralytics YOLO.
        """
        resolved_video_path = Path(video_path).expanduser().resolve()
        if not resolved_video_path.is_file():
            raise VideoAnalysisInferenceError(
                f"Uploaded video does not exist: {resolved_video_path}"
            )

        model = self._get_model()
        fire_frames = 0
        smoke_frames = 0
        maximum_fire_confidence: float | None = None
        maximum_smoke_confidence: float | None = None

        try:
            prediction_frames = model.predict(
                source=str(resolved_video_path),
                stream=True,
                verbose=False,
            )
            for prediction_frame in prediction_frames:
                frame_fire_confidence, frame_smoke_confidence = (
                    self._accepted_frame_confidences(prediction_frame)
                )

                if frame_fire_confidence is not None:
                    fire_frames += 1
                    maximum_fire_confidence = self._maximum_confidence(
                        maximum_fire_confidence, frame_fire_confidence
                    )
                if frame_smoke_confidence is not None:
                    smoke_frames += 1
                    maximum_smoke_confidence = self._maximum_confidence(
                        maximum_smoke_confidence, frame_smoke_confidence
                    )
        except VideoAnalysisInferenceError:
            raise
        except Exception as exc:
            raise VideoAnalysisInferenceError(
                f"YOLO inference failed for uploaded video: {resolved_video_path.name}"
            ) from exc

        if fire_frames >= 3:
            return VideoAnalysisOutcome.FIRE, maximum_fire_confidence
        if smoke_frames >= 1:
            return VideoAnalysisOutcome.SMOKE, maximum_smoke_confidence
        return VideoAnalysisOutcome.NO_DETECTION, None

    def _get_model(self) -> Any:
        """Load and cache the configured checkpoint without importing YOLO at startup."""
        resolved_model_path = self._model_path.expanduser().resolve()
        if not resolved_model_path.is_file():
            raise VideoAnalysisInferenceError(
                f"YOLO checkpoint does not exist: {resolved_model_path}"
            )

        with self._model_cache_lock:
            cached_model = self._model_cache.get(resolved_model_path)
            if cached_model is not None:
                return cached_model

            try:
                from ultralytics import YOLO

                model = YOLO(str(resolved_model_path))
            except Exception as exc:
                raise VideoAnalysisInferenceError(
                    f"Unable to load YOLO checkpoint: {resolved_model_path.name}"
                ) from exc

            self._model_cache[resolved_model_path] = model
            return model

    @staticmethod
    def _accepted_frame_confidences(prediction_frame: Any) -> tuple[float | None, float | None]:
        """Return the strongest qualifying fire and smoke detections in one frame."""
        boxes = getattr(prediction_frame, "boxes", None)
        if boxes is None:
            return None, None

        class_ids = YoloVideoAnalysisAdapter._as_sequence(getattr(boxes, "cls", ()))
        confidences = YoloVideoAnalysisAdapter._as_sequence(getattr(boxes, "conf", ()))
        class_names = getattr(prediction_frame, "names", {})

        frame_fire_confidence: float | None = None
        frame_smoke_confidence: float | None = None
        for class_id, confidence in zip(class_ids, confidences):
            label = YoloVideoAnalysisAdapter._class_label(class_names, class_id)
            confidence_value = float(confidence)

            if label == "fire" and confidence_value >= 0.50:
                frame_fire_confidence = YoloVideoAnalysisAdapter._maximum_confidence(
                    frame_fire_confidence, confidence_value
                )
            elif label == "smoke" and confidence_value >= 0.50:
                frame_smoke_confidence = YoloVideoAnalysisAdapter._maximum_confidence(
                    frame_smoke_confidence, confidence_value
                )

        return frame_fire_confidence, frame_smoke_confidence

    @staticmethod
    def _as_sequence(values: Any) -> Sequence[Any]:
        """Normalize tensor-like YOLO values to a sequence."""
        return values.tolist() if hasattr(values, "tolist") else values

    @staticmethod
    def _class_label(class_names: Any, class_id: Any) -> str:
        """Resolve a YOLO class identifier to a normalized label."""
        class_index = int(class_id)
        if isinstance(class_names, Mapping):
            label = class_names.get(class_index, "")
        elif isinstance(class_names, Sequence) and not isinstance(class_names, str):
            label = class_names[class_index] if class_index < len(class_names) else ""
        else:
            label = ""

        return str(label).strip().casefold()

    @staticmethod
    def _maximum_confidence(
        current: float | None, candidate: float
    ) -> float:
        """Return the greater of an optional current confidence and a candidate."""
        return candidate if current is None else max(current, candidate)
