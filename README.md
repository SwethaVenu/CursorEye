#  CursorEye — Hands-Free Computer Control Using Facial Landmarks

> A real-time, webcam-based assistive technology system that enables complete hands-free computer interaction through facial gestures — no specialized hardware required.

**Bachelor of Engineering Project | Electronics and Communication Engineering**  
College of Engineering Guindy, Anna University, Chennai — April 2025

**Authors:** Swetha V · Abiela Maria Y · Mathisa M

---

## 📖 Table of Contents

- [Overview](#overview)
- [Demo & Screenshots](#demo--screenshots)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Gesture Reference](#gesture-reference)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [How It Works](#how-it-works)
- [Results & Evaluation](#results--evaluation)
- [Limitations](#limitations)
- [Future Scope](#future-scope)
- [Project Report](#project-report)
- [License](#license)

---

## Overview

**CursorEye** is a hands-free Human–Computer Interaction (HCI) system designed primarily for individuals with motor impairments, paralysis, or conditions like ALS. Using only a standard webcam and computer vision, it translates natural facial movements into precise computer commands — no mouse, no keyboard, no extra hardware.

The system uses **MediaPipe FaceMesh** to track 468 facial landmarks in real time and maps them to cursor movement, mouse clicks, scrolling, drag-and-drop, application navigation, and text entry — all through face and eye gestures.

A **Mean Opinion Score (MOS) of 3.97 / 5.0** across 42 participants confirms strong user acceptance, even among first-time users.

---

## Demo & Screenshots

| Feature | Preview |
|---|---|
| Calibration Phase (90%) | Real-time webcam with progress HUD |
| Double Blink → Zoom In (PDF) | Context-aware blink detection |
| Triple Blink → Zoom Out(PDF) , Play/Pause (YouTube/Spotify) | App-specific gesture mapping |
| Eyebrow Lower → Scroll Down | Continuous scroll while held |
| Eyebrow Upper → Scroll Up | Continuous scroll while held |
| Head Tilt → Tab Switch / Slide Nav | Works in Chrome, PPT, VS Code, Excel |
| Eyes Closed 6s → Freeze/Resume | Safety mechanism with progress bar |
| Mouth Open ×3 → Virtual Keyboard | FSSP scanning keyboard |

---

## Features

### 🖱️ Cursor Control
- **Head movement** controls the mouse cursor via nose-tip landmark tracking
- 5-frame moving average smoothing eliminates jitter from micro-movements
- Adaptive calibration personalizes sensitivity to each user's head geometry
- Cursor is clamped to screen boundaries at all times

### 👁️ Blink-Based Clicks
- **Single blink** → Left click
- **Double blink** → Double click (or Zoom In in PDF mode)
- **Triple blink** → Context-specific action (right-click, save, play/pause, etc.)
- Adaptive Eye Aspect Ratio (EAR) threshold — calibrated per user
- 300 ms buffer prevents accidental multi-blink triggers

### 🤨 Eyebrow Scrolling
- **Eyebrow raise** → Scroll up (continuous while held)
- **Eyebrow lower** → Scroll down (continuous while held)
- Ratio-based detection (1.25× raise / 0.85× lower) relative to calibrated baseline
- Suppressed automatically during virtual keyboard sessions

### 😉 Wink Drag-and-Drop
- **Left wink held** for 20+ frames → activates drag mode
- Releasing the wink ends the drag
- Works independently from blink detection

### 🔄 Head Tilt Navigation
- **Tilt right** → Next tab / next slide / next track / forward 10s
- **Tilt left** → Previous tab / previous slide / previous track / rewind 10s
- App-specific cooldowns: 2.5s for documents/editors, 0.8s for media
- Threshold of 0.06 normalized units — robust against involuntary micro-movements

### ❄️ Freeze / Resume
- **Close both eyes for 6 seconds** → toggles between ACTIVE and PAUSED states
- Real-time progress bar displayed during closure
- Automatically releases mouse buttons and closes keyboard on freeze
- 2-second cooldown prevents rapid toggling

### ⌨️ FSSP Virtual Keyboard
- Activated by **opening mouth 3 times** within 3 seconds (MAR > 0.45)
- **Fast scan (0.8s)** cycles through rows
- **Tilt right** to select a row → enters **slow scan (3.5s)** through keys
- **Tilt right** again to type the highlighted key
- **Tilt left** to cancel and return to row scanning
- Supports: uppercase, lowercase, SHIFT, CAPS LOCK, numbers, symbols, arrow keys, ESC, TAB, ENTER, BACKSPACE, DELETE

### 🧠 Context-Aware Application Control
Detects the active foreground application and maps the same gesture to different actions:

| App | Triple Blink | Tilt Right | Tilt Left |
|---|---|---|---|
| Chrome | Right Click | Next Tab | Prev Tab |
| YouTube | Mute | Forward 10s | Rewind 10s |
| Spotify | Play/Pause | Next Track | Prev Track |
| PDF Reader | Zoom Out | — | — |
| PowerPoint | Slideshow | Next Slide | Prev Slide |
| Excel | Enter | Next Sheet | Prev Sheet |
| VS Code | Save | Next Tab | Prev Tab |
| Notepad / Word | Save | — | — |
| Zoom / Teams | Toggle Audio | — | — |
| Desktop | Right Click | — | — |

---

## System Architecture

```
Webcam (640×480 @ 30 FPS)
        │
        ▼
  OpenCV (cv2)
  Frame capture · flip · BGR→RGB
        │
        ▼
  MediaPipe FaceMesh
  468 3D landmark coordinates
        │
        ▼
  NumPy Feature Extraction
  EAR · MAR · Brow distance · Nose XY · Head tilt
        │
        ├──────────────────────┐
        ▼                      ▼
  Cursor Logic            Gesture Classifier
  Smooth + clamp          Blink · Tilt · Brow
        │                      │
        ▼                      ▼
  PyAutoGUI             PyGetWindow
  moveTo(x, y)          Active app → context
                               │
                               ▼
                         ActionHandler
                         gesture + context → OS command
                               │
                               ▼
                         PyAutoGUI
                         click · scroll · hotkey · write
```

The pipeline runs as a single-threaded loop, processing each frame sequentially with no perceptible lag at 30 FPS on commodity hardware (no GPU required).

---

## Gesture Reference

| Gesture | Action |
|---|---|
| Move head | Move cursor |
| Raise eyebrows | Scroll up |
| Lower eyebrows | Scroll down |
| 1 blink | Left click |
| 2 blinks | Double click / Zoom in (PDF) |
| 3 blinks | Context-specific (see table above) |
| Tilt head right | Next tab/slide/track / Forward |
| Tilt head left | Prev tab/slide/track / Rewind |
| Close eyes 6s | Freeze / Resume |
| Open mouth ×3 | Toggle virtual keyboard |
| Tilt right (keyboard) | Select row / type key |
| Tilt left (keyboard) | Cancel → back to row scan |

---

## Tech Stack

| Library | Role |
|---|---|
| `mediapipe` | FaceMesh — 468-point facial landmark inference |
| `opencv-python` | Frame capture, display, UI rendering |
| `numpy` | Geometric feature computation (EAR, MAR, distances) |
| `pyautogui` | OS-level mouse/keyboard injection |
| `pygetwindow` | Active window detection for context awareness |

**Language:** Python 3.8+  
**Platform:** Windows (primary), Linux/macOS with minor adjustments  
**Hardware:** Any standard webcam (720p recommended)

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/SwethaVenu/cursoreye.git
cd cursoreye
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate
```

### 3. Install dependencies

install as a package (recommended):

```bash
pip install -e .
```
Or install dependencies directly:

```bash
pip install opencv-python mediapipe numpy pyautogui pygetwindow
```
Requires Python 3.9+

Install the requirements:

**`requirements`**
```
mediapipe>=0.10.0
opencv-python>=4.8.0
numpy>=1.24.0
pyautogui>=0.9.54
pygetwindow>=0.0.9
```



---

## Usage
if installed as a package:
```bash
face-control
```
Or run directly:
```bash
python run.py
```
Or run as a module:
```bash
python -m face_control
```

### On launch:
1. A webcam window opens and begins **calibration** — keep your face neutral and still
2. Calibration takes ~1.3 seconds (40 frames at 30 FPS)
3. A "Calibration complete! System ACTIVE." message appears in the terminal
4. The system is now fully operational

### To exit:
Press **ESC** in the webcam window.

### Tips for best performance:
- Sit ~50–70 cm from the webcam, face well lit from the front
- Keep your head roughly centered during calibration
- Recalibrate (restart) if you change your seating position significantly
- Avoid flickering light sources — they can cause false blink detection

---

## Configuration

All parameters are centralized in the `Config` dataclass at the top of `final_code.py`:

```python
@dataclass
class Config:
    # Sensitivity
    HEAD_SENSITIVITY: float = 0.18      # Lower = more responsive; higher = smoother
    SCROLL_SPEED: int = 60              # Scroll units per frame
    SMOOTHING_FRAMES: int = 5          # Moving average window for cursor

    # Timing
    DOUBLE_BLINK_INTERVAL: float = 0.5  # Max time between blinks to count as double
    BLINK_WAIT_BUFFER: float = 0.4      # Wait time before dispatching blink action
    ACTION_COOLDOWN: float = 0.8        # Min time between head tilt actions

    # Thresholds
    EAR_THRESHOLD_MULTIPLIER: float = 0.75  # Fraction of mean EAR for blink detection
    BROW_RAISE_THRESHOLD: float = 1.25      # 25% above baseline = scroll up
    BROW_LOWER_THRESHOLD: float = 0.85      # 15% below baseline = scroll down
    HEAD_TILT_THRESHOLD: float = 0.06       # Normalized units for tilt detection
    DRAG_FRAMES_REQUIRED: int = 20          # Frames of wink before drag activates

    # Freeze
    EYES_CLOSED_FREEZE_SECONDS: float = 6.0

    # Virtual Keyboard
    MAR_THRESHOLD: float = 0.45             # Mouth open detection threshold
    MOUTH_OPEN_COUNT_REQUIRED: int = 3      # Mouth cycles to toggle keyboard
    FSSP_FAST_SCAN_INTERVAL: float = 0.8    # Row scan speed (seconds)
    FSSP_SLOW_SCAN_INTERVAL: float = 3.5    # Column scan speed (seconds)
```

---

## How It Works

### Eye Aspect Ratio (EAR)
Blink detection uses the ratio of vertical to horizontal eye distances:

```
EAR = d(p159, p145) / d(p33, p133)   [left eye]
EAR = d(p386, p374) / d(p362, p263)  [right eye]
EAR_avg = (EAR_left + EAR_right) / 2
```

A blink is detected when `EAR_avg < 0.75 × mean_EAR` (calibrated per user).

### Mouth Aspect Ratio (MAR)
```
MAR = d(p13, p14) / d(p78, p308)
```
Mouth-open event fires when `MAR > 0.45`.

### Nose-to-Screen Mapping
```
Δx = nose_x − ref_x
screen_x = interp(Δx, [−S, S], [0, W])   where S = 0.18
```
The reference position is anchored at calibration and re-anchored on resume.

### Eyebrow Detection
```
D_brow = d(p105, p159)
Raise: D_brow > μ_brow × 1.25
Lower: D_brow < μ_brow × 0.85
```

### Head Tilt Detection
```
Tilt = y_263 − y_33   (right eye corner Y − left eye corner Y)
Right tilt: Tilt > 0.06
Left tilt:  Tilt < −0.06
```

---

## Results & Evaluation

Tested on a standard laptop with built-in 720p webcam under indoor lighting:

| Metric | Result |
|---|---|
| Frame rate | Stable 30 FPS for sessions up to 45 min |
| Calibration time | ~1.33 seconds (40 frames) |
| Cursor target acquisition | 2–4s for 32×32 px icons on 1080p display |
| Blink false activations | None observed under stable lighting |
| Head tilt false activations | None (0.06 threshold above natural noise) |
| Freeze false triggers | None (6s threshold conservatively safe) |
| Keyboard activation accuracy | No unintended triggers during speech/movement |

### MOS Evaluation (42 participants)

| Section | Mean Score | Rating |
|---|---|---|
| Head Tracking | 3.97 | Good |
| Blink Control | 3.93 | Good |
| Eyebrow & Head Tilt | 4.01 | ⭐ Strong |
| Context Awareness | 3.96 | Good |
| Virtual Keyboard | 3.90 | Good |
| Freeze / Resume | **4.10** | ⭐ Strong |
| Usability & Comfort | 3.96 | Good |
| Overall Satisfaction | 3.98 | Good |
| **Overall MOS** | **3.97 / 5.0** | **Good** |

Score distribution: 79.8% rated "Good" (4), 11.6% "Fair" (3), 8.6% "Excellent" (5). No scores below 3 were recorded.

---

## Limitations

- **Lighting sensitivity:** EAR-based blink detection is susceptible to rapid lighting changes (flickering lights, sudden glare)
- **Fixed scan rates:** FSSP keyboard timing (0.8s rows, 3.5s columns) is not yet adaptive to individual reaction speeds
- **Window title matching:** Context detection may fail for non-standard titles, web apps with dynamic titles, or non-Windows environments
- **Single-user design:** System processes only the first detected face
- **No motor-impaired user trials yet:** Formal evaluation with the target population is planned for future work

---

## Future Scope

- Integration with OS accessibility APIs for more robust context detection
- Dynamic FSSP scan rate adjustment based on per-user interaction patterns
- Machine learning models for personalized gesture thresholds
- Multi-monitor support and extended display handling
- Gaze direction estimation for finer cursor precision
- Extensive usability trials with motor-impaired users against established accessibility benchmarks

---

## Project Report

The full project report (`reportttt.pdf`) is included in this repository and covers:

- Complete mathematical formulations for EAR, MAR, nose mapping, brow detection, and head tilt
- Detailed system architecture and module descriptions
- All results tables, figures, and MOS analysis
- Literature review and motivation

---

## Citation

If you use this project in your research or build upon it, please cite:

```
Swetha V, Abiela Maria Y, Mathisa M. "CursorEye: Hands-Free Computer Cursor Control
Using Facial Landmarks." B.E. Project Report, Department of Electronics and
Communication Engineering, College of Engineering Guindy, Anna University,
Chennai, April 2025.
```

---

## Acknowledgements

We thank **Dr. T. Manimekalai** (Project Supervisor) , Department of ECE, College of Engineering Guindy, Anna University, for their guidance and support throughout this project.

---

## License

This project is licensed under the **MIT License** — free to use, modify, and distribute with attribution. See [LICENSE](LICENSE) for details.

---

