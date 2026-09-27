"""ANPR (Automatic Number Plate Recognition) detector.

Uses a YOLOv8 model to locate licence plates in a frame, then crops each
detected region and runs EasyOCR to extract the plate text.

Model loading
-------------
Looks for weights at ``models/plate_best.pt`` (relative to this package root).
Override via the ``PLATE_MODEL_PATH`` environment variable.
Falls back gracefully to a mock if the file is absent.

EasyOCR is initialised **lazily** — only on the first actual call to
``read_plate()`` or ``_real_detect()``.  This means startup is instant even
when EasyOCR has never been run before and needs to download its language
model (~100 MB), because that download only happens when a real plate model
is loaded *and* a detection is triggered.

Output contract
---------------
Same as all other detectors:
    detect(frame, frame_index) -> list[dict]

Each dict contains:
    type              – "plate_detected"
    label             – "plate_detected"
    confidence        – detection confidence (float)
    bbox              – [x1, y1, x2, y2] of the plate region
    plate_number      – OCR result string  (e.g. "TN09AB1234")
    ocr_confidence    – EasyOCR character-level confidence (float, 0–1)
    severity          – None (plates are informational, not severity-graded)

The ``read_plate(frame, bbox)`` helper is also public so TrackingDetector
(and main.py) can run ANPR on a specific region of interest without going
through the full plate-detection step.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "plate_best.pt"
_DEFAULT_OCR_MODEL_DIR = Path(__file__).resolve().parents[1] / "models" / "easyocr"


class ANPRDetector:
    """Detect and read licence plates, with mock fallback when weights absent.

    EasyOCR is initialised lazily on first use so startup is always instant.
    """

    def __init__(
        self,
        model_path: str | Path | None = None,
        confidence_threshold: float = 0.40,
    ) -> None:
        if model_path is None:
            model_path = os.getenv("PLATE_MODEL_PATH", str(_DEFAULT_MODEL_PATH))

        self._model_path = Path(model_path)
        self._conf = confidence_threshold
        self._yolo = None
        self._ocr = None          # loaded lazily on first read_plate() call
        self._ocr_attempted = False  # guard so we only try once
        self._using_mock = False

        self._load_model()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _load_model(self) -> None:
        """Try to load the YOLOv8 plate-detection weights."""
        if not self._model_path.exists():
            logger.warning(
                "Plate model weights not found at %s, using mock ANPR detector - "
                "see README for how to add a real model",
                self._model_path,
            )
            print(
                f"[ANPRDetector] WARNING: Plate model weights not found at "
                f"{self._model_path}, using mock ANPR detector - "
                f"see README for how to add a real model"
            )
            self._using_mock = True
            return

        try:
            from ultralytics import YOLO  # noqa: PLC0415

            self._yolo = YOLO(str(self._model_path))
            print(f"[ANPRDetector] Loaded plate detection model from {self._model_path}")
        except Exception as exc:  # noqa: BLE001
            logger.error("[ANPRDetector] Failed to load plate model (%s); mock mode.", exc)
            print(
                f"[ANPRDetector] ERROR loading plate model ({exc}); "
                f"falling back to mock."
            )
            self._using_mock = True

    def _ensure_ocr(self) -> bool:
        """Lazily initialise EasyOCR on first call. Returns True if ready."""
        if self._ocr is not None:
            return True
        if self._ocr_attempted:
            return False  # already failed once, don't retry

        self._ocr_attempted = True
        try:
            import easyocr  # noqa: PLC0415

            print("[ANPRDetector] Initialising EasyOCR (may download models on first run)...")
            # gpu=False: CPU-only; set True if CUDA is available
            _DEFAULT_OCR_MODEL_DIR.mkdir(parents=True, exist_ok=True)
            self._ocr = easyocr.Reader(
                ["en"],
                gpu=False,
                verbose=False,
                model_storage_directory=str(_DEFAULT_OCR_MODEL_DIR),
                user_network_directory=str(_DEFAULT_OCR_MODEL_DIR),
            )
            print("[ANPRDetector] EasyOCR ready.")
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("[ANPRDetector] EasyOCR unavailable (%s).", exc)
            print(
                f"[ANPRDetector] WARNING: EasyOCR unavailable ({exc}). "
                f"Install with: pip install easyocr"
            )
            return False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(self, frame, frame_index: int | None = None) -> list[dict]:
        """Run full plate detection + OCR on a frame."""
        if self._using_mock:
            return self._mock_detect(frame_index)
        try:
            return self._real_detect(frame)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[ANPRDetector] detect() error: %s", exc)
            return []

    def read_plate(self, frame, bbox: list[float]) -> tuple[str, float]:
        """OCR a specific bbox region; returns (plate_text, ocr_confidence).

        Call this when the plate location is already known (e.g. from a
        tracking incident event) to avoid running a second full YOLO pass.
        Returns ("", 0.0) if OCR is unavailable, in mock mode, or fails.
        """
        if self._using_mock:
            return ("", 0.0)
        if not self._ensure_ocr():
            return ("", 0.0)
        try:
            return self._run_ocr(frame, bbox)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[ANPRDetector] read_plate() error: %s", exc)
            return ("", 0.0)

    # ------------------------------------------------------------------
    # Detection implementations
    # ------------------------------------------------------------------

    def _real_detect(self, frame) -> list[dict]:
        results = self._yolo(frame, conf=self._conf, verbose=False)
        if not results:
            return []

        self._ensure_ocr()  # lazy-init OCR now that we have real detections

        detections: list[dict] = []
        for box in results[0].boxes:
            x1, y1, x2, y2 = (round(float(v), 1) for v in box.xyxy[0])
            conf = float(box.conf[0])
            plate_text, ocr_conf = self._run_ocr(frame, [x1, y1, x2, y2])
            detections.append(
                {
                    "type": "plate_detected",
                    "label": "plate_detected",
                    "confidence": conf,
                    "bbox": [x1, y1, x2, y2],
                    "plate_number": plate_text,
                    "ocr_confidence": ocr_conf,
                    "severity": None,
                }
            )
        return detections

    def _run_ocr(self, frame, bbox: list[float]) -> tuple[str, float]:
        """Crop bbox from frame and return (text, confidence)."""
        if self._ocr is None:
            return ("", 0.0)

        x1, y1, x2, y2 = (int(v) for v in bbox)
        crop = frame[max(y1, 0) : max(y2, 1), max(x1, 0) : max(x2, 1)]
        if crop.size == 0:
            return ("", 0.0)

        ocr_results = self._ocr.readtext(crop)
        if not ocr_results:
            return ("", 0.0)

        best = max(ocr_results, key=lambda r: r[2])
        text = best[1].strip().upper().replace(" ", "")
        conf = round(float(best[2]), 3)
        return (text, conf)

    def _mock_detect(self, frame_index: int | None) -> list[dict]:
        """Return a clearly fake plate every 40th frame."""
        if frame_index and frame_index % 40 == 0:
            print(
                "[ANPRDetector] MOCK DATA: returning fake plate 'MOCK-0000'. "
                "Add real weights to enable actual ANPR."
            )
            return [
                {
                    "type": "plate_detected",
                    "label": "plate_detected",
                    "confidence": 0.5,
                    "bbox": [100.0, 200.0, 300.0, 260.0],
                    "plate_number": "MOCK-0000",
                    "ocr_confidence": 0.5,
                    "severity": None,
                }
            ]
        return []
