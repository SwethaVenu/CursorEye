"""Central configuration for the Face Control System."""

from dataclasses import dataclass


@dataclass
class Config:
    """Central configuration for all face control settings."""

    # Display
    WINDOW_WIDTH: int = 640
    WINDOW_HEIGHT: int = 480

    # Sensitivity
    HEAD_SENSITIVITY: float = 0.18
    SCROLL_SPEED: int = 60
    SMOOTHING_FRAMES: int = 5

    # Timing
    DOUBLE_BLINK_INTERVAL: float = 0.5
    BLINK_WAIT_BUFFER: float = 0.4
    ACTION_COOLDOWN: float = 0.8
    CALIBRATION_FRAMES: int = 40

    # Thresholds
    BROW_RAISE_THRESHOLD: float = 1.25
    BROW_LOWER_THRESHOLD: float = 0.85
    EAR_THRESHOLD_MULTIPLIER: float = 0.75
    DRAG_FRAMES_REQUIRED: int = 20
    HEAD_TILT_THRESHOLD: float = 0.06
    HEAD_NOD_DOWN_THRESHOLD: float = 1.25  # ratio above baseline = nod down
    HEAD_NOD_COOLDOWN: float = 1.5

    # Freeze toggle: Close eyes for 6 seconds
    EYES_CLOSED_FREEZE_SECONDS: float = 6.0

    # FSSP Virtual Keyboard — mouth open x3 toggle + scan intervals
    MAR_THRESHOLD: float = 0.45
    MOUTH_OPEN_COUNT_REQUIRED: int = 3
    MOUTH_OPEN_INTERVAL: float = 3.0
    KEYBOARD_TOGGLE_COOLDOWN: float = 3.0
    FSSP_FAST_SCAN_INTERVAL: float = 0.8
    FSSP_SLOW_SCAN_INTERVAL: float = 3.5
    KEYBOARD_NOD_COOLDOWN: float = 1.5


config = Config()
