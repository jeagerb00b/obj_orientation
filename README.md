# Object Orientation Detection using Computer Vision

A ROS 2 Humble package that detects objects from a live webcam feed and estimates their
orientation angle in real time using Principal Component Analysis (PCA).

Built as part of ROMI robobt reqruitment in my college.

---

## Demo

Place any elongated object (pen, ruler, key) on a plain white background in front of
your webcam. The system detects the object and overlays:

- **Cyan outline** — detected contour
- **Orange box** — minimum-area rotated bounding box
- **Green arrow** — major PCA axis (orientation direction)
- **Blue arrow** — minor PCA axis
- **Angle label** — orientation in degrees, normalised to `[-90°, 90°]`

> 0° = horizontal &nbsp;|&nbsp; ±90° = vertical &nbsp;|&nbsp; 45° = diagonal

---

## How It Works

```
webcam_publisher  ──►  /camera/image_raw  ──►  orientation_detector  ──►  /orientation/image  ──►  display_node
                                                        │
                                                        └──►  /orientation/angles  (Float64 array)
```

### Detection pipeline (inside `orientation_detector`)

1. Convert frame to **grayscale** → **Gaussian blur** (7×7)
2. **Otsu thresholding** → binary mask (auto-picks the best global threshold)
3. **Morphological close** (fill holes) + **open** (remove noise)
4. `findContours` → filter by area (`min_area` / `max_area`)
5. For each valid contour — **PCA on the point cloud**:
   - Compute covariance matrix of all contour points
   - `np.linalg.eigh` → eigenvalues + eigenvectors
   - Major eigenvector angle = object orientation
   - Normalise to `[-90°, 90°]`
6. Annotate frame → publish on `/orientation/image`
7. Publish angle list on `/orientation/angles`

---

## Prerequisites

| Requirement | Version |
|---|---|
| OS | Ubuntu 22.04 LTS |
| ROS 2 | Humble Hawksbill |
| Python | 3.10 |
| OpenCV (apt) | 4.5.4 |

Install dependencies:

```bash
sudo apt update
sudo apt install -y ros-humble-cv-bridge python3-opencv
```

> **Important:** do **not** install `opencv-python` via `pip` alongside the apt package.
> Having both causes silent crashes. If you already have it, remove it:
> ```bash
> pip uninstall -y opencv-python opencv-python-headless
> ```

---

## Installation

```bash
# Clone the repo
git clone https://github.com/jeagerboob/orientation-detection.git
cd orientation-detection

# Source ROS 2
source /opt/ros/humble/setup.bash

# Build
colcon build --packages-select orientation_detection

# Source the workspace
source install/setup.bash
```

---

## Running

```bash
ros2 launch orientation_detection detection.launch.py
```

A window titled **"Object Orientation Detection"** will open.
- It immediately shows **"Waiting for camera frames..."** — this confirms the display layer is working.
- Within a second it switches to your live annotated webcam feed.
- Press **Q** in the window to quit.

### Watch angle values in a second terminal

```bash
source install/setup.bash
ros2 topic echo /orientation/angles
```

---

## Configuration

Parameters are set in `launch/detection.launch.py`:

| Parameter | Default | Description |
|---|---|---|
| `device_id` | `0` | Camera device index (`/dev/video0`) |
| `fps` | `30.0` | Webcam capture frame rate |
| `min_area` | `1500` | Minimum contour area in pixels² (increase to filter noise) |
| `max_area` | `300000` | Maximum contour area in pixels² (decrease to exclude background) |
| `invert_thresh` | `False` | Set `True` for light objects on dark backgrounds |

Override at runtime without editing the launch file:

```bash
ros2 launch orientation_detection detection.launch.py min_area:=5000
```

---

## ROS Topics

| Topic | Type | Direction | Description |
|---|---|---|---|
| `/camera/image_raw` | `sensor_msgs/Image` | webcam_publisher → detector | Raw BGR webcam frames |
| `/orientation/image` | `sensor_msgs/Image` | detector → display_node | Annotated output frame |
| `/orientation/angles` | `std_msgs/Float64MultiArray` | detector → any | Detected angles in degrees |

---

## Project Structure

```
orientation_detection/
├── orientation_detection/
│   ├── __init__.py
│   ├── webcam_publisher.py     # Reads webcam → publishes /camera/image_raw
│   ├── detector_node.py        # PCA detection → publishes annotated image + angles
│   └── display_node.py         # Subscribes to /orientation/image → cv2.imshow
├── launch/
│   └── detection.launch.py     # Launches all three nodes
├── resource/
│   └── orientation_detection
├── package.xml
├── setup.cfg
└── setup.py
```

---

## Troubleshooting

**Camera LED turns on but no frames arrive**

Force the V4L2 backend explicitly (already done in this version):
```bash
# verify
grep "CAP_V4L2" orientation_detection/webcam_publisher.py
```

**Wrong camera device**

List devices and try a different index:
```bash
ls /dev/video*
# then in detection.launch.py set: 'device_id': 2
```

**Noise / too many detections**

Increase `min_area` in `detection.launch.py` (e.g. `5000`) or place the object on a plain white A4 sheet.

**Object not detected**

- Decrease `min_area` if the object is small
- Set `invert_thresh: True` if your object is lighter than the background
- Ensure good lighting and avoid shadows across the object

**Circular/square objects give unstable angles**

Expected behaviour — PCA orientation is undefined for symmetric shapes. Use elongated objects (pen, ruler, key, screwdriver).

**Window doesn't appear**

Ensure `$DISPLAY` is set and you are running in a desktop session, not over SSH without X11 forwarding:
```bash
echo $DISPLAY   # should print :0 or similar
```

---

## Deliverables (Phase 2 Task Requirements)

| Requirement | Status |
|---|---|
| Detect object from webcam feed | ✅ |
| Calculate orientation angle | ✅ |
| Display detected angle on output | ✅ |
| Source code | ✅ |
| GitHub repository | ✅ |
| Demonstration video | ✅ |
| Short documentation | ✅ this README |
| **Bonus** — real-time webcam implementation | ✅ |
| **Bonus** — detect multiple objects | ✅ |

---

## License

MIT License — see [LICENSE](LICENSE) for details.
