"""Run direct plate detection and OCR on one image.

Usage:
    python test_anpr.py path/to/image.jpg
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2

from detectors.anpr_detector import ANPRDetector


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test ANPR on a single image.")
    parser.add_argument("image", type=Path, help="Path to the input image")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    frame = cv2.imread(str(args.image))
    if frame is None:
        raise SystemExit(f"Unable to read image: {args.image}")

    detector = ANPRDetector()
    if detector._using_mock:
        print("Mode: MOCK (models/plate_best.pt was not loaded)")
        print("Plate found: no -- real detection and OCR were not run")
        return

    print(f"Mode: REAL (loaded {detector._model_path})")
    # Intentionally call the underlying full YOLO + OCR path directly. This test
    # does not use any incident-gating logic from a pipeline or tracker.
    detections = detector._real_detect(frame)

    if not detections:
        print("Plate found: no")
        return

    print(f"Plate found: yes ({len(detections)} detection(s))")
    for index, detection in enumerate(detections, start=1):
        print(f"Plate {index} text: {detection['plate_number'] or '<not read>'}")
        print(f"Plate {index} detection confidence: {detection['confidence']:.3f}")
        print(f"Plate {index} OCR confidence: {detection['ocr_confidence']:.3f}")


if __name__ == "__main__":
    main()
