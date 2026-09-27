# Detection Engine

Standalone onboard AI-processing module for Urban Fleet AI. It samples frames from
a bus video, detects COCO vehicle classes with YOLOv8, generates simulated Chennai
GPS positions, and posts events to the local backend.

## Setup

From this directory, create and activate a virtual environment, then install the
dependencies:

```bash
python -m venv .venv
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
```

Place an input video in `sample_videos/`. The first run downloads the small
pretrained `yolov8n.pt` model automatically.

Start the platform backend on port 8000 first, then run:

```bash
python main.py --video sample_videos/test.mp4 --bus_id BUS-001
```

By default, detection runs once every 10 frames. Increase the interval to reduce
compute further, or reduce it for more frequent observations:

```bash
python main.py --video sample_videos/test.mp4 --bus_id BUS-001 --frame_interval 5
```

`VehicleDetector` returns cars, buses, trucks, and motorcycles from YOLOv8's COCO
model. `PotholeDetector` uses the identical `detect(frame, frame_index)` contract,
but currently returns one mock pothole every 50th frame. Replace its implementation
with a custom-trained or Roboflow pothole model without changing `main.py`.

Each API event contains the backend's full required schema: event type, simulated
Chennai GPS, confidence, ISO timestamp, bus ID, and optional severity or vehicle
count. The module logs each successful event submission and continues processing if
an API submission fails.
