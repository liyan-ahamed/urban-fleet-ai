"""Pothole detection using locally trained YOLOv8 weights."""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "pothole_best.pt"


class PotholeDetector:
    """Detect potholes with real YOLO inference, with a missing-weights fallback."""

    def __init__(
        self,
        model_path: str | Path | None = None,
        confidence_threshold: float = 0.25,
    ) -> None:
        if model_path is None:
            model_path = os.getenv("POTHOLE_MODEL_PATH", str(_DEFAULT_MODEL_PATH))

        self._model_path = Path(model_path)
        self._conf = confidence_threshold
        self._yolo = None
        self._using_mock = False
        self._load_model()

    def _load_model(self) -> None:
        """Try to load the trained pothole-detection weights."""
        if not self._model_path.exists():
            logger.warning("Pothole model weights not found at %s; using mock mode.", self._model_path)
            print(
                f"[PotholeDetector] WARNING: Pothole model weights not found at "
                f"{self._model_path}, using mock detector."
            )
            self._using_mock = True
            return

        try:
            from ultralytics import YOLO  # noqa: PLC0415

            self._yolo = YOLO(str(self._model_path))
            print(f"[PotholeDetector] Loaded pothole detection model from {self._model_path}")
        except Exception as exc:  # noqa: BLE001
            logger.error("[PotholeDetector] Failed to load pothole model (%s); mock mode.", exc)
            print(f"[PotholeDetector] ERROR loading pothole model ({exc}); falling back to mock.")
            self._using_mock = True

    def detect(self, frame, frame_index: int | None = None) -> list[dict]:
        """Return real pothole detections, or a clearly marked mock fallback."""
        if self._using_mock:
            return self._mock_detect(frame, frame_index)
        try:
            return self._real_detect(frame)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[PotholeDetector] detect() error: %s", exc)
            return []

    def _real_detect(self, frame) -> list[dict]:
        """Run YOLO inference using the loaded pothole weights."""
        results = self._yolo(frame, conf=self._conf, verbose=False)
        if not results:
            return []

        detections: list[dict] = []
        for box in results[0].boxes:
            x1, y1, x2, y2 = (round(float(value), 1) for value in box.xyxy[0])
            confidence = float(box.conf[0])
            class_name = results[0].names[int(box.cls[0])]
            detections.append(
                {
                    "type": "pothole",
                    "label": class_name,
                    "confidence": confidence,
                    "bbox": [x1, y1, x2, y2],
                    "severity": self._severity(confidence),
                }
            )
        return detections

    @staticmethod
    def _severity(confidence: float) -> str:
        if confidence >= 0.70:
            return "high"
        if confidence >= 0.45:
            return "medium"
        return "low"

    @staticmethod
    def _mock_detect(frame, frame_index: int | None) -> list[dict]:
        """Return a clearly fake event only when real weights are unavailable."""
        if frame_index and frame_index % 50 == 0:
            height, width = frame.shape[:2]
            print("[PotholeDetector] MOCK DATA: returning fake pothole event.")
            return [
                {
                    "type": "pothole",
                    "label": "pothole",
                    "confidence": 0.72,
                    "bbox": [width * 0.35, height * 0.60, width * 0.55, height * 0.78],
                    "severity": "medium",
                }
            ]
        return []
