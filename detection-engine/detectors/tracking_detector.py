"""Vehicle tracking and simple incident heuristics built on a shared YOLOv8 model."""

from __future__ import annotations

from collections import defaultdict, deque
import os

from detectors.vehicle_detector import VEHICLE_CLASSES


def _env_float(name: str, default: float) -> float:
    """Read a positive float configuration value from the environment."""
    try:
        value = float(os.getenv(name, default))
        return value if value > 0 else default
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    """Read a positive integer configuration value from the environment."""
    try:
        value = int(os.getenv(name, default))
        return value if value > 0 else default
    except ValueError:
        return default


class TrackingDetector:
    """Track COCO vehicles with ByteTrack and emit heuristic incident events.

    ``model`` must be the already-loaded YOLO instance owned by ``VehicleDetector``.
    Calling ``model.track(..., persist=True)`` preserves ByteTrack's state between
    sampled frames without loading another set of YOLO weights.
    """

    def __init__(
        self,
        model,
        confidence_threshold: float = 0.35,
        history_size: int = 10,
        rash_driving_threshold: float | None = None,
        overlap_threshold: float | None = None,
        incident_window_frames: int | None = None,
        required_overlap_samples: int | None = None,
        required_missing_samples: int | None = None,
        edge_margin_fraction: float | None = None,
    ) -> None:
        self.model = model
        self.confidence_threshold = confidence_threshold
        self.history_size = history_size
        self.rash_driving_threshold = rash_driving_threshold or _env_float(
            "RASH_DRIVING_THRESHOLD", 60.0
        )
        self.overlap_threshold = overlap_threshold or _env_float("COLLISION_OVERLAP_THRESHOLD", 0.60)
        self.incident_window_frames = incident_window_frames or _env_int(
            "HIT_AND_RUN_WINDOW_FRAMES", 30
        )
        self.required_overlap_samples = required_overlap_samples or _env_int(
            "COLLISION_OVERLAP_SAMPLES", 2
        )
        self.required_missing_samples = required_missing_samples or _env_int(
            "HIT_AND_RUN_MISSING_SAMPLES", 3
        )
        self.edge_margin_fraction = edge_margin_fraction or _env_float(
            "HIT_AND_RUN_EDGE_MARGIN", 0.15
        )
        self._positions: dict[int, deque[tuple[float, float, int]]] = defaultdict(
            lambda: deque(maxlen=self.history_size)
        )
        self._recent_overlaps: list[dict] = []
        self._last_event_frame: dict[tuple[str, int], int] = {}

    def detect(self, frame, frame_index: int | None = None) -> list[dict]:
        """Run ByteTrack and return rash-driving / hit-and-run event dictionaries."""
        current_frame = frame_index or 0
        result = self.model.track(
            frame,
            conf=self.confidence_threshold,
            persist=True,
            tracker="bytetrack.yaml",
            verbose=False,
        )[0]

        vehicles = self._tracked_vehicles(result)
        current_ids = set(vehicles)
        events = self._resolve_recent_overlaps(
            current_ids, vehicles, current_frame, frame.shape[1], frame.shape[0]
        )

        for vehicle_id, vehicle in vehicles.items():
            previous = self._positions[vehicle_id][-1] if self._positions[vehicle_id] else None
            displacement = 0.0
            if previous is not None:
                displacement = ((vehicle["center"][0] - previous[0]) ** 2 + (vehicle["center"][1] - previous[1]) ** 2) ** 0.5

            self._positions[vehicle_id].append((*vehicle["center"], current_frame))
            if displacement > self.rash_driving_threshold and self._can_emit(
                "rash_driving", vehicle_id, current_frame
            ):
                confidence = min(
                    1.0,
                    vehicle["confidence"] * (displacement / self.rash_driving_threshold),
                )
                events.append(
                    self._event("rash_driving", vehicle, vehicle_id, confidence, displacement)
                )

        self._record_overlaps(vehicles, current_frame)
        self._trim_state(current_ids, current_frame)
        return events

    def _tracked_vehicles(self, result) -> dict[int, dict]:
        """Convert tracked YOLO boxes into an ID-indexed vehicle mapping."""
        if result.boxes is None or result.boxes.id is None:
            return {}

        vehicles: dict[int, dict] = {}
        for box in result.boxes:
            class_name = result.names[int(box.cls[0])]
            if class_name not in VEHICLE_CLASSES or box.id is None:
                continue
            vehicle_id = int(box.id[0])
            x1, y1, x2, y2 = (round(float(value), 1) for value in box.xyxy[0])
            vehicles[vehicle_id] = {
                "label": class_name,
                "confidence": float(box.conf[0]),
                "bbox": [x1, y1, x2, y2],
                "center": ((x1 + x2) / 2, (y1 + y2) / 2),
            }
        return vehicles

    def _record_overlaps(self, vehicles: dict[int, dict], frame_index: int) -> None:
        """Remember sustained, high-overlap vehicle contact candidates."""
        items = list(vehicles.items())
        for index, (first_id, first) in enumerate(items):
            for second_id, second in items[index + 1 :]:
                overlap = self._overlap_ratio(first["bbox"], second["bbox"])
                if overlap < self.overlap_threshold:
                    continue
                ids = tuple(sorted((first_id, second_id)))
                existing = next(
                    (candidate for candidate in self._recent_overlaps if candidate["ids"] == ids),
                    None,
                )
                if existing is None:
                    self._recent_overlaps.append(
                        {
                            "frame": frame_index,
                            "last_overlap_frame": frame_index,
                            "ids": ids,
                            "vehicles": {first_id: first.copy(), second_id: second.copy()},
                            "overlap": overlap,
                            "overlap_samples": 1,
                            "missing_samples": defaultdict(int),
                        }
                    )
                elif frame_index > existing["last_overlap_frame"]:
                    existing["last_overlap_frame"] = frame_index
                    existing["overlap"] = max(existing["overlap"], overlap)
                    existing["overlap_samples"] += 1
                    existing["vehicles"] = {first_id: first.copy(), second_id: second.copy()}

    def _resolve_recent_overlaps(
        self,
        current_ids: set[int],
        vehicles: dict[int, dict],
        frame_index: int,
        frame_width: int,
        frame_height: int,
    ) -> list[dict]:
        """Flag sustained contact followed by a confirmed non-edge disappearance."""
        events: list[dict] = []
        retained: list[dict] = []
        for candidate in self._recent_overlaps:
            age = frame_index - candidate["last_overlap_frame"]
            if age <= 0:
                retained.append(candidate)
                continue
            if age > self.incident_window_frames:
                continue

            if candidate["overlap_samples"] < self.required_overlap_samples:
                retained.append(candidate)
                continue

            for vehicle_id in candidate["ids"]:
                before = candidate["vehicles"][vehicle_id]
                other_id = next(identifier for identifier in candidate["ids"] if identifier != vehicle_id)
                if vehicle_id not in current_ids:
                    candidate["missing_samples"][vehicle_id] += 1
                    if (
                        candidate["missing_samples"][vehicle_id] >= self.required_missing_samples
                        and other_id in current_ids
                        and not self._near_frame_edge(before["bbox"], frame_width, frame_height)
                        and self._can_emit("hit_and_run", vehicle_id, frame_index)
                    ):
                        events.append(
                            self._event(
                                "hit_and_run",
                                before,
                                vehicle_id,
                                min(1.0, before["confidence"] * candidate["overlap"]),
                                None,
                            )
                        )
                else:
                    candidate["missing_samples"][vehicle_id] = 0
            if not any(
                count >= self.required_missing_samples
                for count in candidate["missing_samples"].values()
            ):
                retained.append(candidate)
        self._recent_overlaps = retained
        return events

    def _can_emit(self, event_type: str, vehicle_id: int, frame_index: int) -> bool:
        """Avoid repeatedly sending the same vehicle's incident every sampled frame."""
        key = (event_type, vehicle_id)
        last_frame = self._last_event_frame.get(key)
        if last_frame is not None and frame_index - last_frame < self.incident_window_frames:
            return False
        self._last_event_frame[key] = frame_index
        return True

    def _trim_state(self, current_ids: set[int], frame_index: int) -> None:
        stale_ids = [
            vehicle_id
            for vehicle_id, positions in self._positions.items()
            if vehicle_id not in current_ids and positions and frame_index - positions[-1][2] > self.incident_window_frames
        ]
        for vehicle_id in stale_ids:
            del self._positions[vehicle_id]

    @staticmethod
    def _event(
        event_type: str,
        vehicle: dict,
        vehicle_id: int,
        confidence: float,
        displacement: float | None,
    ) -> dict:
        event = {
            "type": event_type,
            "label": vehicle["label"],
            "confidence": round(confidence, 3),
            "bbox": vehicle["bbox"],
            "tracked_vehicle_id": vehicle_id,
        }
        if displacement is not None:
            event["displacement"] = round(displacement, 1)
        return event

    @staticmethod
    def _distance(first: tuple[float, float], second: tuple[float, float]) -> float:
        return ((first[0] - second[0]) ** 2 + (first[1] - second[1]) ** 2) ** 0.5

    def _near_frame_edge(self, bbox: list[float], frame_width: int, frame_height: int) -> bool:
        """Ignore disappearances that are plausibly normal exits from the view."""
        center_x = (bbox[0] + bbox[2]) / 2
        center_y = (bbox[1] + bbox[3]) / 2
        margin_x = frame_width * self.edge_margin_fraction
        margin_y = frame_height * self.edge_margin_fraction
        return (
            center_x < margin_x
            or center_x > frame_width - margin_x
            or center_y < margin_y
            or center_y > frame_height - margin_y
        )

    @staticmethod
    def _overlap_ratio(first: list[float], second: list[float]) -> float:
        left = max(first[0], second[0])
        top = max(first[1], second[1])
        right = min(first[2], second[2])
        bottom = min(first[3], second[3])
        intersection = max(0.0, right - left) * max(0.0, bottom - top)
        first_area = max(0.0, first[2] - first[0]) * max(0.0, first[3] - first[1])
        second_area = max(0.0, second[2] - second[0]) * max(0.0, second[3] - second[1])
        return intersection / min(first_area, second_area) if min(first_area, second_area) else 0.0
