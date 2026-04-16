"""FSSP (Fast Slow Scan Process) virtual keyboard rendered with OpenCV."""

import time
from typing import Optional

import cv2
import numpy as np
import pyautogui

from .config import config
from .enums import KeyboardState


class FSSPVirtualKeyboard:
    """Fast Slow Scan Process Virtual Keyboard.

    Row scanning (fast) → tilt right to select row →
    Column scanning (slow) → tilt right to type key.
    Tilt left to cancel column scan.
    Mouth open x3 to toggle open/close (handled by FaceController).
    """

    KEYBOARD_LAYOUT = [
        ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'BKSP'],
        ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', 'DEL'],
        ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ';', 'ENTER'],
        ['Z', 'X', 'C', 'V', 'B', 'N', 'M', ',', '.', '/', 'SHIFT'],
        ['ESC', 'TAB', 'CAPS', '  SPACE  ', 'LEFT', 'RIGHT', 'UP', 'DOWN', 'CLOSE'],
    ]

    SPECIAL_KEYS = {
        'BKSP': 'backspace',
        'DEL': 'delete',
        'ENTER': 'enter',
        'SHIFT': 'shift',
        'ESC': 'escape',
        'TAB': 'tab',
        'CAPS': 'capslock',
        '  SPACE  ': 'space',
        'LEFT': 'left',
        'RIGHT': 'right',
        'UP': 'up',
        'DOWN': 'down',
        'CLOSE': None,
    }

    def __init__(self):
        self.state = KeyboardState.HIDDEN
        self.current_row = 0
        self.current_col = 0
        self.last_scan_time = 0.0
        self.last_select_time = 0.0
        self.last_nod_type_time = 0.0
        self.base_nose_y = None
        self.shift_active = False
        self.caps_active = False

        self.keyboard_window_name = "FSSP Virtual Keyboard"
        self.window_created = False

        self.key_width = 60
        self.key_height = 50
        self.key_margin = 4
        self.keyboard_padding = 10

        max_cols = max(len(row) for row in self.KEYBOARD_LAYOUT)
        num_rows = len(self.KEYBOARD_LAYOUT)

        self.keyboard_width = (
            (self.key_width + self.key_margin) * max_cols + self.keyboard_padding * 2
        )
        self.keyboard_height = (
            (self.key_height + self.key_margin) * num_rows + self.keyboard_padding * 2 + 40
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def show(self):
        if not self.window_created:
            cv2.namedWindow(self.keyboard_window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(self.keyboard_window_name, self.keyboard_width, self.keyboard_height)
            cv2.setWindowProperty(self.keyboard_window_name, cv2.WND_PROP_TOPMOST, 1)
            self.window_created = True
        self.state = KeyboardState.ROW_SCANNING
        self.current_row = 0
        self.current_col = 0
        self.last_scan_time = time.time()
        print(">>> KEYBOARD OPENED - Row Scanning <<<")

    def hide(self):
        self.state = KeyboardState.HIDDEN
        if self.window_created:
            cv2.destroyWindow(self.keyboard_window_name)
            self.window_created = False
        print(">>> KEYBOARD CLOSED <<<")

    def toggle(self):
        if self.state == KeyboardState.HIDDEN:
            self.show()
        else:
            self.hide()

    def is_visible(self) -> bool:
        return self.state != KeyboardState.HIDDEN

    # ------------------------------------------------------------------
    # Scanning
    # ------------------------------------------------------------------

    def update_scan(self) -> None:
        if self.state == KeyboardState.HIDDEN:
            return
        now = time.time()
        if self.state == KeyboardState.ROW_SCANNING:
            if now - self.last_scan_time >= config.FSSP_FAST_SCAN_INTERVAL:
                self.current_row = (self.current_row + 1) % len(self.KEYBOARD_LAYOUT)
                self.last_scan_time = now
        elif self.state == KeyboardState.COLUMN_SCANNING:
            if now - self.last_scan_time >= config.FSSP_SLOW_SCAN_INTERVAL:
                row_length = len(self.KEYBOARD_LAYOUT[self.current_row])
                self.current_col = (self.current_col + 1) % row_length
                self.last_scan_time = now

    def select(self) -> None:
        """Blinks during keyboard are ignored — use head tilt instead."""
        return None

    def check_tilt_select(self, tilt: float) -> Optional[str]:
        """Head tilt RIGHT selects a row or types the highlighted key."""
        if self.state == KeyboardState.HIDDEN:
            return None
        now = time.time()
        if now - self.last_nod_type_time < config.KEYBOARD_NOD_COOLDOWN:
            return None

        if tilt > config.HEAD_TILT_THRESHOLD:
            self.last_nod_type_time = now

            if self.state == KeyboardState.ROW_SCANNING:
                self.state = KeyboardState.COLUMN_SCANNING
                self.current_col = 0
                self.last_scan_time = now
                print(f">>> Row {self.current_row + 1} selected - TILT RIGHT to type <<<")
                return None

            elif self.state == KeyboardState.COLUMN_SCANNING:
                key = self.KEYBOARD_LAYOUT[self.current_row][self.current_col]
                typed_char = self._execute_key(key)
                if self.state != KeyboardState.HIDDEN:
                    self.state = KeyboardState.ROW_SCANNING
                    self.current_row = 0
                    self.last_scan_time = now
                return typed_char
        return None

    def cancel_to_row_scan(self):
        """Cancel column scanning (triggered by head tilt left)."""
        if self.state == KeyboardState.COLUMN_SCANNING:
            self.state = KeyboardState.ROW_SCANNING
            self.current_row = 0
            self.last_scan_time = time.time()
            self.base_nose_y = None
            print(">>> Cancelled - Back to Row Scanning <<<")

    # ------------------------------------------------------------------
    # Key execution
    # ------------------------------------------------------------------

    def _execute_key(self, key: str) -> Optional[str]:
        if key == 'CLOSE':
            self.hide()
            return None
        if key == 'SHIFT':
            self.shift_active = not self.shift_active
            print(f">>> SHIFT {'ON' if self.shift_active else 'OFF'} <<<")
            return None
        if key == 'CAPS':
            self.caps_active = not self.caps_active
            print(f">>> CAPS LOCK {'ON' if self.caps_active else 'OFF'} <<<")
            return None
        if key in self.SPECIAL_KEYS:
            special = self.SPECIAL_KEYS[key]
            if special:
                pyautogui.press(special)
                print(f">>> Pressed: {special.upper()} <<<")
            return None

        char = key
        if char.isalpha():
            if self.caps_active != self.shift_active:
                char = char.upper()
            else:
                char = char.lower()
        elif self.shift_active:
            shift_map = {
                '1': '!', '2': '@', '3': '#', '4': '$', '5': '%',
                '6': '^', '7': '&', '8': '*', '9': '(', '0': ')',
                ',': '<', '.': '>', '/': '?', ';': ':',
            }
            char = shift_map.get(char, char)

        pyautogui.write(char, interval=0)
        print(f">>> Typed: {char} <<<")

        if self.shift_active and key not in ['SHIFT', 'CAPS']:
            self.shift_active = False

        return char

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self) -> np.ndarray:
        img = np.zeros((self.keyboard_height, self.keyboard_width, 3), dtype=np.uint8)
        img[:] = (30, 30, 30)

        # Status bar
        if self.state == KeyboardState.ROW_SCANNING:
            status_text = "ROW SCAN - TILT RIGHT to select row"
            status_color = (0, 255, 255)
        elif self.state == KeyboardState.COLUMN_SCANNING:
            current_key = self.KEYBOARD_LAYOUT[self.current_row][self.current_col]
            status_text = f"TILT RIGHT to type '{current_key}' | Tilt LEFT=Cancel"
            status_color = (0, 255, 0)
        else:
            status_text = ""
            status_color = (150, 150, 150)

        cv2.rectangle(img, (0, 0), (self.keyboard_width, 35), (50, 50, 50), -1)
        cv2.putText(img, status_text, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 1)

        indicators = []
        if self.shift_active:
            indicators.append("SHIFT")
        if self.caps_active:
            indicators.append("CAPS")
        if indicators:
            indicator_text = " | ".join(indicators)
            cv2.putText(
                img, indicator_text, (self.keyboard_width - 150, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 165, 0), 1,
            )

        y_offset = 45
        for row_idx, row in enumerate(self.KEYBOARD_LAYOUT):
            x = self.keyboard_padding
            y = y_offset + row_idx * (self.key_height + self.key_margin)

            for col_idx, key in enumerate(row):
                kw = (
                    self.key_width * 2 + self.key_margin
                    if key == '  SPACE  '
                    else self.key_width
                )

                if self.state == KeyboardState.ROW_SCANNING and row_idx == self.current_row:
                    key_color = (0, 100, 200)
                    text_color = (255, 255, 255)
                elif self.state == KeyboardState.COLUMN_SCANNING:
                    if row_idx == self.current_row and col_idx == self.current_col:
                        key_color = (0, 255, 0)
                        text_color = (0, 0, 0)
                    elif row_idx == self.current_row:
                        key_color = (60, 60, 60)
                        text_color = (200, 200, 200)
                    else:
                        key_color = (50, 50, 50)
                        text_color = (150, 150, 150)
                else:
                    key_color = (60, 60, 60)
                    text_color = (200, 200, 200)

                if key in ['SHIFT', 'CAPS'] and (
                    (key == 'SHIFT' and self.shift_active)
                    or (key == 'CAPS' and self.caps_active)
                ):
                    key_color = (0, 165, 255)

                if key == 'CLOSE':
                    if not (
                        self.state == KeyboardState.COLUMN_SCANNING
                        and row_idx == self.current_row
                        and col_idx == self.current_col
                    ):
                        key_color = (0, 0, 150)

                cv2.rectangle(img, (x, y), (x + kw, y + self.key_height), key_color, -1)
                cv2.rectangle(img, (x, y), (x + kw, y + self.key_height), (100, 100, 100), 1)

                display_key = key
                if key.isalpha() and len(key) == 1:
                    display_key = (
                        key.upper() if self.caps_active != self.shift_active else key.lower()
                    )

                text_size = cv2.getTextSize(display_key, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                text_x = x + (kw - text_size[0]) // 2
                text_y = y + (self.key_height + text_size[1]) // 2
                cv2.putText(
                    img, display_key, (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1,
                )

                x += kw + self.key_margin

        return img

    def update_and_render(self) -> None:
        if not self.is_visible():
            return
        self.update_scan()
        keyboard_img = self.render()
        cv2.imshow(self.keyboard_window_name, keyboard_img)
