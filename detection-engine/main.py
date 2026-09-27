"""Run onboard video detection and publish events to the Urban Fleet API."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import cv2

from detectors.anpr_detector import ANPRDetector
from detectors.pothole_detector import PotholeDetector
from detectors.pedestrian_detector import PedestrianDetector
from detectors.tracking_detector import TrackingDetector
from detectors.vehicle_detector import VehicleDetector
from utils.api_client import post_event
from utils.gps_simulator import GPSSimulator


def make_event(
    event_type: str,
    lat: float,
    lng: float,
    confidence: float,
    bus_id: str,
    *,
    severity: str | None = None,
    vehicle_count: int | None = None,
    plate_number: str | None = None,
) -> dict:
    """Build a payload accepted by the backend POST /events endpoint."""
    return {
        "type": event_type,
        "lat": lat,
        "lng": lng,
        "confidence": confidence,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "bus_id": bus_id,
        "plate_number": plate_number,
        "severity": severity,
        "vehicle_count": vehicle_count,
    }


def send_event(event: dict) -> None:
    """Post an event and print an outcome without stopping video processing."""
    try:
        post_event(event)
        print(
            f"Sent {event['type']} event | bus={event['bus_id']} "
            f"gps=({event['lat']:.5f}, {event['lng']:.5f}) "
            f"confidence={event['confidence']:.2f}"
        )
    except Exception as error:
        print(f"Could not send {event['type']} event: {error}")


def process_video(video_path: Path, bus_id: str, frame_interval: int) -> None:
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"Unable to open video: {video_path}")

    vehicle_detector = VehicleDetector()
    pedestrian_detector = PedestrianDetector(vehicle_detector.model)
    tracking_detector = TrackingDetector(vehicle_detector.model)
    anpr_detector = ANPRDetector()
    pothole_detector = PotholeDetector()
    gps = GPSSimulator()
    frame_index = 0

    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break

            frame_index += 1
            if frame_index % frame_interval != 0:
                continue

            lat, lng = gps.next_position()
            vehicles = vehicle_detector.detect(frame, frame_index)
            vehicle_count = len(vehicles)

            # A sampled frame becomes a traffic-density observation, including zero
            # vehicles so downstream analytics can distinguish quiet roads.
            vehicle_confidence = max(
                (detection["confidence"] for detection in vehicles), default=0.0
            )
            send_event(
                make_event(
                    "vehicle_density",
                    lat,
                    lng,
                    vehicle_confidence,
                    bus_id,
                    vehicle_count=vehicle_count,
                )
            )

            for incident in tracking_detector.detect(frame, frame_index):
                plate_number, ocr_confidence = anpr_detector.read_plate(
                    frame, incident["bbox"]
                )
                print(
                    f"Tracking {incident['type']} | vehicle_id="
                    f"{incident['tracked_vehicle_id']} | "
                    f"plate={plate_number or '<unread>'} | ocr={ocr_confidence:.2f}"
                )
                send_event(
                    make_event(
                        incident["type"],
                        lat,
                        lng,
                        incident["confidence"],
                        bus_id,
                        plate_number=plate_number or None,
                    )
                )

            for detection in pedestrian_detector.detect(frame, frame_index):
                send_event(
                    make_event(
                        detection["type"],
                        lat,
                        lng,
                        detection["confidence"],
                        bus_id,
                    )
                )

            for detection in pothole_detector.detect(frame, frame_index):
                send_event(
                    make_event(
                        "pothole",
                        lat,
                        lng,
                        detection["confidence"],
                        bus_id,
                        severity=detection.get("severity"),
                    )
                )
    finally:
        capture.release()

    print(f"Finished processing {frame_index} frames from {video_path.name}.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect urban events in a bus video.")
    parser.add_argument("--video", required=True, type=Path, help="Path to an input video")
    parser.add_argument("--bus_id", required=True, help="Identifier for the source bus")
    parser.add_argument(
        "--frame_interval",
        type=int,
        default=10,
        help="Run detectors every N frames (default: 10)",
    )
    args = parser.parse_args()
    if args.frame_interval < 1:
        parser.error("--frame_interval must be at least 1")
    return args


if __name__ == "__main__":
    arguments = parse_args()
    process_video(arguments.video, arguments.bus_id, arguments.frame_interval)
