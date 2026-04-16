"""Main face controller: camera loop, calibration, gesture dispatch."""

import time
from collections import deque
from typing import Optional

import cv2
import mediapipe as mp1
import numpy as np
import pyautogui

from .actions import ActionHandler
from .config import config
from .enums import AppContext, ControlState, KeyboardState
from .keyboard import FSSPVirtualKeyboard
from .utils import dist, get_context, get_ear, get_mar


class FaceController:
    """Main face control system for motor-impaired users."""

    def __init__(self):
        pyautogui.PAUSE = 0
        pyautogui.FAILSAFE = True
        self.screen_w, self.screen_h = pyautogui.size()

        # MediaPipe
        self.mp_face = mp1.solutions.face_mesh
        self.face_mesh = self.mp_face.FaceMesh(
            refine_landmarks=True,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5,
        )

        # Camera
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        # Window
        self.window_name = "Face Control (Press ESC to exit)"
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        cv2.setWindowProperty(self.window_name, cv2.WND_PROP_TOPMOST, 1)

        # State
        self.state = ControlState.CALIBRATING
        self.x_hist = deque(maxlen=config.SMOOTHING_FRAMES)
        self.y_hist = deque(maxlen=config.SMOOTHING_FRAMES)
        self.ref_nose_x: Optional[float] = None
        self.ref_nose_y: Optional[float] = None

        # Calibration
        self.ear_history: list = []
        self.brow_history: list = []
        self.nod_history: list = []
        self.adaptive_ear_thresh = 0.0
        self.base_brow_dist = 0.0
        self.base_nod_value = 0.0
        self.last_nod_time = 0.0

        # Blink
        self.blink_count = 0
        self.last_blink_time = 0.0
        self.eye_closed = False

        # Drag
        self.is_dragging = False
        self.drag_frames = 0

        # Action timing
        self.last_action_time = 0.0

        # Freeze / resume
        self.last_state_toggle = 0.0
        self.STATE_TOGGLE_COOLDOWN = 2.0
        self.eyes_closed_start: Optional[float] = None
        self.eyes_closed_progress = 0.0

        # Action handler and virtual keyboard
        self.action_handler = ActionHandler()
        self.keyboard = FSSPVirtualKeyboard()

        # Mouth open x3 toggle
        self.mouth_open: bool = False
        self.mouth_open_count: int = 0
        self.mouth_open_last_time: float = 0.0
        self.last_mouth_toggle_time: float = 0.0

        # Action display
        self.action_display_text: str = ""
        self.action_display_time: float = 0.0
        self.ACTION_DISPLAY_DURATION: float = 3.0

    # ------------------------------------------------------------------
    # Calibration
    # ------------------------------------------------------------------

    def calibrate(self, lm) -> bool:
        avg_ear = get_ear(lm)[2]
        current_brow_dist = dist(lm[105], lm[159])
        eye_mid_y = (lm[33].y + lm[263].y) / 2
        nod_value = lm[4].y - eye_mid_y

        self.ear_history.append(avg_ear)
        self.brow_history.append(current_brow_dist)
        self.nod_history.append(nod_value)

        if len(self.ear_history) >= config.CALIBRATION_FRAMES:
            self.adaptive_ear_thresh = (
                np.mean(self.ear_history) * config.EAR_THRESHOLD_MULTIPLIER
            )
            self.base_brow_dist = np.mean(self.brow_history)
            self.base_nod_value = np.mean(self.nod_history)
            return True
        return False

    # ------------------------------------------------------------------
    # Freeze toggle
    # ------------------------------------------------------------------

    def check_freeze_toggle(self, lm) -> bool:
        now = time.time()
        if now - self.last_state_toggle < self.STATE_TOGGLE_COOLDOWN:
            self.eyes_closed_progress = 0.0
            return False

        _, _, avg_ear = get_ear(lm)
        if avg_ear < self.adaptive_ear_thresh:
            if self.eyes_closed_start is None:
                self.eyes_closed_start = now
            closed_duration = now - self.eyes_closed_start
            self.eyes_closed_progress = min(
                closed_duration / config.EYES_CLOSED_FREEZE_SECONDS, 1.0
            )
            if closed_duration >= config.EYES_CLOSED_FREEZE_SECONDS:
                self.eyes_closed_start = None
                self.eyes_closed_progress = 0.0
                self.last_state_toggle = now
                return True
        else:
            self.eyes_closed_start = None
            self.eyes_closed_progress = 0.0
        return False

    # ------------------------------------------------------------------
    # Cursor
    # ------------------------------------------------------------------

    def process_cursor_movement(self, lm):
        nose = lm[4]
        if self.ref_nose_x is None:
            self.ref_nose_x, self.ref_nose_y = nose.x, nose.y

        tx = np.interp(
            nose.x - self.ref_nose_x,
            [-config.HEAD_SENSITIVITY, config.HEAD_SENSITIVITY],
            [0, self.screen_w],
        )
        ty = np.interp(
            nose.y - self.ref_nose_y,
            [-config.HEAD_SENSITIVITY, config.HEAD_SENSITIVITY],
            [0, self.screen_h],
        )

        self.x_hist.append(tx)
        self.y_hist.append(ty)
        smooth_x = max(0, min(self.screen_w - 1, np.mean(self.x_hist)))
        smooth_y = max(0, min(self.screen_h - 1, np.mean(self.y_hist)))
        pyautogui.moveTo(smooth_x, smooth_y)

    # ------------------------------------------------------------------
    # Brow scroll
    # ------------------------------------------------------------------

    def process_brow_scroll(self, lm):
        current_brow_dist = dist(lm[105], lm[159])
        if current_brow_dist > self.base_brow_dist * config.BROW_RAISE_THRESHOLD:
            pyautogui.scroll(config.SCROLL_SPEED)
            self.set_action_display("Scroll Up")
        elif current_brow_dist < self.base_brow_dist * config.BROW_LOWER_THRESHOLD:
            pyautogui.scroll(-config.SCROLL_SPEED)
            self.set_action_display("Scroll Down")

    # ------------------------------------------------------------------
    # Mouth open x3 keyboard toggle
    # ------------------------------------------------------------------

    def check_mouth_toggle(self, lm) -> bool:
        """Detect 3 mouth open-close cycles to toggle the virtual keyboard."""
        now = time.time()
        if now - self.last_mouth_toggle_time < config.KEYBOARD_TOGGLE_COOLDOWN:
            self.mouth_open = False
            return False

        mar = get_mar(lm)

        if mar > config.MAR_THRESHOLD:
            if not self.mouth_open:
                self.mouth_open = True
        elif self.mouth_open:
            self.mouth_open = False
            if now - self.mouth_open_last_time < config.MOUTH_OPEN_INTERVAL:
                self.mouth_open_count += 1
            else:
                self.mouth_open_count = 1
            self.mouth_open_last_time = now

            if self.mouth_open_count >= config.MOUTH_OPEN_COUNT_REQUIRED:
                was_visible = self.keyboard.is_visible()
                self.keyboard.toggle()

                self.mouth_open_count = 0
                self.last_mouth_toggle_time = now
                self.blink_count = 0
                self.last_blink_time = now

                if was_visible:
                    self.last_action_time = now
                    self.set_action_display("Keyboard Closed")
                    print(">>> MOUTH x3 - KEYBOARD CLOSED <<<")
                else:
                    self.set_action_display("Keyboard Opened")
                    print(">>> MOUTH x3 - KEYBOARD OPENED <<<")
                return True

        if self.mouth_open_count > 0 and now - self.mouth_open_last_time > config.MOUTH_OPEN_INTERVAL:
            self.mouth_open_count = 0

        return False

    # ------------------------------------------------------------------
    # Blinks
    # ------------------------------------------------------------------

    def process_blinks(self, lm, context: AppContext):
        now = time.time()
        left_ear, right_ear, avg_ear = get_ear(lm)

        if avg_ear < self.adaptive_ear_thresh:
            if not self.eye_closed:
                self.eye_closed = True
        else:
            if self.eye_closed:
                self.eye_closed = False

                if self.keyboard.is_visible():
                    self.keyboard.select()
                    return

                if now - self.last_blink_time < config.DOUBLE_BLINK_INTERVAL:
                    self.blink_count += 1
                else:
                    self.blink_count = 1
                self.last_blink_time = now

        if not self.keyboard.is_visible():
            if self.blink_count > 0 and (now - self.last_blink_time > config.BLINK_WAIT_BUFFER):
                self.action_handler.execute_blink_action(context, self.blink_count)
                self.set_action_display(self.action_handler.last_action_label)
                self.blink_count = 0

        # Wink-hold drag
        if not self.keyboard.is_visible():
            if left_ear < self.adaptive_ear_thresh and right_ear > self.adaptive_ear_thresh:
                self.drag_frames += 1
                if self.drag_frames >= config.DRAG_FRAMES_REQUIRED and not self.is_dragging:
                    pyautogui.mouseDown()
                    self.is_dragging = True
                    self.set_action_display("Drag Started")
            else:
                if self.is_dragging:
                    pyautogui.mouseUp()
                    self.is_dragging = False
                    self.set_action_display("Drag Released")
                self.drag_frames = 0

    # ------------------------------------------------------------------
    # Head tilt
    # ------------------------------------------------------------------

    def process_head_tilt(self, lm, context: AppContext):
        tilt = lm[263].y - lm[33].y

        if self.keyboard.is_visible():
            typed = self.keyboard.check_tilt_select(tilt)
            if typed:
                self.set_action_display(f"Typed: {typed}")
            if self.keyboard.state == KeyboardState.COLUMN_SCANNING:
                if tilt < -config.HEAD_TILT_THRESHOLD:
                    now = time.time()
                    if now - self.last_action_time >= config.ACTION_COOLDOWN:
                        self.keyboard.cancel_to_row_scan()
                        self.set_action_display("KB: Cancelled")
                        self.last_action_time = now
            return

        if tilt > config.HEAD_TILT_THRESHOLD:
            prev = self.last_action_time
            self.last_action_time = self.action_handler.execute_head_tilt_action(
                context, "right", self.last_action_time
            )
            if self.last_action_time != prev:
                self.set_action_display(self.action_handler.last_action_label)
        elif tilt < -config.HEAD_TILT_THRESHOLD:
            prev = self.last_action_time
            self.last_action_time = self.action_handler.execute_head_tilt_action(
                context, "left", self.last_action_time
            )
            if self.last_action_time != prev:
                self.set_action_display(self.action_handler.last_action_label)

    # ------------------------------------------------------------------
    # Head nod down (YouTube play/pause)
    # ------------------------------------------------------------------

    def process_head_nod(self, lm, context: AppContext):
        if self.keyboard.is_visible():
            return
        now = time.time()
        if now - self.last_nod_time < config.HEAD_NOD_COOLDOWN:
            return

        eye_mid_y = (lm[33].y + lm[263].y) / 2
        nod_value = lm[4].y - eye_mid_y
        nod_ratio = nod_value / max(self.base_nod_value, 0.001)

        if nod_ratio > config.HEAD_NOD_DOWN_THRESHOLD:
            self.last_nod_time = now
            if context == AppContext.YOUTUBE:
                pyautogui.press('space')
                self.set_action_display("Play/Pause")

    # ------------------------------------------------------------------
    # Action display helper
    # ------------------------------------------------------------------

    def set_action_display(self, text: str):
        self.action_display_text = text
        self.action_display_time = time.time()

    # ------------------------------------------------------------------
    # UI overlay
    # ------------------------------------------------------------------

    def draw_ui(self, frame, context: AppContext, lm=None):
        h, w = frame.shape[:2]
        now = time.time()

        CONTEXT_MODE_NAMES = {
            AppContext.PDF: "PDF READING MODE",
            AppContext.CHROME: "CHROME BROWSING MODE",
            AppContext.YOUTUBE: "YOUTUBE VIDEO MODE",
            AppContext.EXPLORER: "FILE EXPLORER MODE",
            AppContext.VSCODE: "VSCODE CODING MODE",
            AppContext.WORD: "WORD DOCUMENT MODE",
            AppContext.EXCEL: "EXCEL SPREADSHEET MODE",
            AppContext.POWERPOINT: "POWERPOINT PRESENTATION MODE",
            AppContext.NOTEPAD: "NOTEPAD EDITING MODE",
            AppContext.SPOTIFY: "SPOTIFY MUSIC MODE",
            AppContext.ZOOM: "ZOOM MEETING MODE",
            AppContext.TEAMS: "TEAMS MEETING MODE",
            AppContext.DESKTOP: "DESKTOP MODE",
        }

        # Top bar: status
        if self.state == ControlState.PAUSED:
            status_color = (0, 0, 255)
            status_text = "PAUSED"
        elif self.state == ControlState.CALIBRATING:
            status_color = (0, 255, 255)
            progress = len(self.ear_history) / config.CALIBRATION_FRAMES * 100
            status_text = f"CALIBRATING {progress:.0f}%"
        else:
            status_color = (0, 255, 0)
            status_text = "ACTIVE"

        cv2.rectangle(frame, (0, 0), (w, 40), (40, 40, 40), -1)
        cv2.putText(frame, status_text, (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)

        # Context mode name (top bar, right side)
        if self.state == ControlState.ACTIVE:
            mode_name = CONTEXT_MODE_NAMES.get(context, "DESKTOP MODE")
            if self.keyboard.is_visible():
                mode_name = "KEYBOARD INPUT MODE"
            elif self.is_dragging:
                mode_name = "DRAG MODE"
            mode_size = cv2.getTextSize(mode_name, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            cv2.putText(
                frame, mode_name, (w - mode_size[0] - 10, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1,
            )

        # Action display (top-left, stays for 3 s)
        if self.action_display_text and (now - self.action_display_time < self.ACTION_DISPLAY_DURATION):
            action_y = 70
            text_size = cv2.getTextSize(self.action_display_text, cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2)[0]
            cv2.rectangle(
                frame,
                (8, action_y - text_size[1] - 8),
                (text_size[0] + 20, action_y + 8),
                (0, 0, 0), -1,
            )
            cv2.putText(
                frame, self.action_display_text, (12, action_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2,
            )

        # Keyboard sub-mode hint (bottom)
        if self.keyboard.is_visible() and self.state == ControlState.ACTIVE:
            if self.keyboard.state == KeyboardState.ROW_SCANNING:
                kb_text = "Row Scanning - TILT RIGHT to select"
                kb_color = (0, 200, 255)
            elif self.keyboard.state == KeyboardState.COLUMN_SCANNING:
                key = self.keyboard.KEYBOARD_LAYOUT[self.keyboard.current_row][self.keyboard.current_col]
                kb_text = f"Select [{key}] - TILT RIGHT to type"
                kb_color = (0, 255, 0)
            else:
                kb_text = "Keyboard Active"
                kb_color = (0, 200, 255)
            cv2.putText(frame, kb_text, (12, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, kb_color, 1)

        # Eyes-closed freeze progress bar
        if self.eyes_closed_progress > 0:
            bar_width = int(180 * self.eyes_closed_progress)
            bar_x = w // 2 - 90
            bar_y = h - 50
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + 180, bar_y + 24), (50, 50, 50), -1)
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + 24), (0, 255, 255), -1)
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + 180, bar_y + 24), (255, 255, 255), 2)
            secs = int(self.eyes_closed_progress * 6)
            cv2.putText(
                frame, f"FREEZE: {secs}/6s", (bar_x + 45, bar_y + 17),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1,
            )

        # Paused overlay
        if self.state == ControlState.PAUSED:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 100), -1)
            cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
            cv2.putText(
                frame, "PAUSED", (w // 2 - 80, h // 2 - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3,
            )
            cv2.putText(
                frame, "Close eyes 6s to resume", (w // 2 - 130, h // 2 + 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1,
            )

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        print("=" * 60)
        print("   FACE CONTROL SYSTEM FOR MOTOR-IMPAIRED USERS")
        print("=" * 60)
        print("\nMOUSE CONTROLS:")
        print("  - Move head.............. Control cursor")
        print("  - Raise eyebrows......... Scroll up")
        print("  - Lower eyebrows......... Scroll down")
        print("  - 1 blink................ Left click")
        print("  - 2 blinks............... Select (double-click) / Zoom in (PDF)")
        print("  - 3 blinks............... Context action (right-click/save/zoom out)")
        print("  - Left wink (hold)....... Drag")
        print("  - Tilt head left/right... Tab/page switch / Rewind-Forward (YouTube)")
        print("")
        print("SYSTEM CONTROLS:")
        print("  - Open mouth x3.......... TOGGLE VIRTUAL KEYBOARD (within 3s)")
        print("  >>> FREEZE/RESUME: Close eyes for 6 seconds <<<")
        print("")
        print("FSSP VIRTUAL KEYBOARD:")
        print("  - Open mouth x3.......... Open/close keyboard")
        print("  - Tilt head right........ Select row / type key")
        print("  - Tilt head left......... Cancel (back to row scan)")
        print("")
        print("Calibrating... Keep face neutral for 2 seconds.")
        print("Press ESC to exit.\n")

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Could not read from camera")
                break

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_frame)
            context = get_context()

            lm = None
            if results.multi_face_landmarks:
                lm = results.multi_face_landmarks[0].landmark

                if self.state == ControlState.CALIBRATING:
                    if self.calibrate(lm):
                        self.state = ControlState.ACTIVE
                        self.ref_nose_x = lm[4].x
                        self.ref_nose_y = lm[4].y
                        print("Calibration complete! System ACTIVE.")
                        print("To PAUSE: Close eyes for 6 seconds")
                        print("To OPEN KEYBOARD: Open mouth 3 times")
                else:
                    if self.check_freeze_toggle(lm):
                        if self.state == ControlState.PAUSED:
                            self.state = ControlState.ACTIVE
                            self.ref_nose_x = lm[4].x
                            self.ref_nose_y = lm[4].y
                            self.blink_count = 0
                            self.eye_closed = False
                            self.drag_frames = 0
                            self.set_action_display("RESUMED")
                            print(">>> RESUMED <<<")
                        elif self.state == ControlState.ACTIVE:
                            self.state = ControlState.PAUSED
                            if self.is_dragging:
                                pyautogui.mouseUp()
                                self.is_dragging = False
                            if self.keyboard.is_visible():
                                self.keyboard.hide()
                            self.blink_count = 0
                            self.eye_closed = False
                            self.drag_frames = 0
                            self.set_action_display("PAUSED")
                            print(">>> PAUSED <<<")

                    elif self.state == ControlState.ACTIVE:
                        self.check_mouth_toggle(lm)

                        if not self.keyboard.is_visible():
                            self.process_cursor_movement(lm)
                            self.process_brow_scroll(lm)

                        self.process_blinks(lm, context)
                        self.process_head_tilt(lm, context)
                        self.process_head_nod(lm, context)

                        self.keyboard.update_and_render()

            self.draw_ui(frame, context, lm)
            cv2.imshow(self.window_name, frame)

            if cv2.waitKey(1) & 0xFF == 27:
                break

        # Cleanup
        if self.is_dragging:
            pyautogui.mouseUp()
        if self.keyboard.is_visible():
            self.keyboard.hide()
        self.cap.release()
        cv2.destroyAllWindows()
        print("\nFace Control System terminated.")
