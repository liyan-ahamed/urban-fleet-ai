"""YOLOv8 vehicle detection."""

from __future__ import annotations

from ultralytics import YOLO


VEHICLE_CLASSES = {"car", "bus", "truck", "motorcycle"}


class VehicleDetector:
    """Detect COCO vehicle classes with the small pretrained YOLOv8 model."""

    def __init__(self, model_name: str = "yolov8n.pt", confidence_threshold: float = 0.35):
        # Ultralytics downloads this pretrained model automatically when absent.
        self.model = YOLO(model_name)
        self.confidence_threshold = confidence_threshold

    def detect(self, frame, frame_index: int | None = None) -> list[dict]:
        """Return vehicle detections in the common detector output shape."""
        result = self.model(frame, conf=self.confidence_threshold, verbose=False)[0]
        detections: list[dict] = []
        for box in result.boxes:
            class_name = result.names[int(box.cls[0])]
            if class_name not in VEHICLE_CLASSES:
                continue
            x1, y1, x2, y2 = (round(float(value), 1) for value in box.xyxy[0])
            detections.append(
                {
                    "type": "vehicle",
                    "label": class_name,
                    "confidence": float(box.conf[0]),
                    "bbox": [x1, y1, x2, y2],
                }
            )
        return detections
