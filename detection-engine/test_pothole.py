"""Run direct pothole detection on one image.

Usage:
    python test_pothole.py path/to/image.jpg
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2

from detectors.pothole_detector import PotholeDetector


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test pothole detection on one image.")
    parser.add_argument("image", type=Path, help="Path to the input image")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    frame = cv2.imread(str(args.image))
    if frame is None:
        raise SystemExit(f"Unable to read image: {args.image}")

    detector = PotholeDetector()
    if detector._using_mock:
        print("Mode: MOCK (models/pothole_best.pt was not loaded)")
        print("Pothole found: no -- real inference was not run")
        return

    print(f"Mode: REAL (loaded {detector._model_path})")
    detections = detector._real_detect(frame)
    if not detections:
        print("Pothole found: no")
        return

    print(f"Pothole found: yes ({len(detections)} detection(s))")
    for index, detection in enumerate(detections, start=1):
        print(f"Pothole {index} confidence: {detection['confidence']:.3f}")
        print(f"Pothole {index} bbox: {detection['bbox']}")
        print(f"Pothole {index} severity: {detection['severity']}")


if __name__ == "__main__":
    main()
