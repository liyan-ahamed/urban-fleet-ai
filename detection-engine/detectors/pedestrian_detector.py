"""Pedestrian-risk detection using a shared YOLOv8 COCO model."""

from __future__ import annotations


PERSON_CLASS = "person"


class PedestrianDetector:
    """Flag groups of people detected in the road-facing center of a frame.

    The model is supplied by the caller so this detector shares the existing
    YOLOv8 instance instead of loading another copy of ``yolov8n.pt``.
    """

    def __init__(
        self,
        model,
        confidence_threshold: float = 0.35,
        center_band: tuple[float, float] = (0.30, 0.70),
        minimum_people: int = 2,
    ):
        if not 0 <= center_band[0] < center_band[1] <= 1:
            raise ValueError("center_band values must be ordered fractions from 0 to 1")
        if minimum_people < 2:
            raise ValueError("minimum_people must be at least 2")

        self.model = model
        self.confidence_threshold = confidence_threshold
        self.center_band = center_band
        self.minimum_people = minimum_people

    def detect(self, frame, frame_index: int | None = None) -> list[dict]:
        """Return one risk event when a central-frame person group is found."""
        frame_width = frame.shape[1]
        band_left = frame_width * self.center_band[0]
        band_right = frame_width * self.center_band[1]
        result = self.model(frame, conf=self.confidence_threshold, verbose=False)[0]

        people: list[dict] = []
        for box in result.boxes:
            class_name = result.names[int(box.cls[0])]
            if class_name != PERSON_CLASS:
                continue

            x1, y1, x2, y2 = (float(value) for value in box.xyxy[0])
            horizontal_center = (x1 + x2) / 2
            if not band_left <= horizontal_center <= band_right:
                continue

            people.append(
                {
                    "confidence": float(box.conf[0]),
                    "bbox": [x1, y1, x2, y2],
                }
            )

        if len(people) < self.minimum_people:
            return []

        boxes = [person["bbox"] for person in people]
        cluster_bbox = [
            round(min(box[0] for box in boxes), 1),
            round(min(box[1] for box in boxes), 1),
            round(max(box[2] for box in boxes), 1),
            round(max(box[3] for box in boxes), 1),
        ]
        return [
            {
                "type": "pedestrian_risk",
                "label": "person_cluster",
                "confidence": sum(person["confidence"] for person in people) / len(people),
                "bbox": cluster_bbox,
                "person_count": len(people),
            }
        ]
