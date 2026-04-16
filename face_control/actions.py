"""Context-aware action handler for blink and head-tilt gestures."""

import time

import pyautogui

from .config import config
from .enums import AppContext


class ActionHandler:
    """Dispatches blink and head-tilt events to the correct OS action
    based on the currently active application context."""

    def __init__(self):
        self.last_action_label: str = ""

    def execute_blink_action(self, context: AppContext, blink_count: int):
        triple_labels = {
            AppContext.PDF: "Zoom Out",
            AppContext.CHROME: "Right Click",
            AppContext.YOUTUBE: "Mute",
            AppContext.EXPLORER: "Go Up",
            AppContext.VSCODE: "Save",
            AppContext.WORD: "Save",
            AppContext.EXCEL: "Enter",
            AppContext.POWERPOINT: "Slideshow",
            AppContext.NOTEPAD: "Save",
            AppContext.SPOTIFY: "Play/Pause",
            AppContext.ZOOM: "Toggle Audio",
            AppContext.TEAMS: "Toggle Mute",
        }

        if context == AppContext.PDF:
            if blink_count == 1:
                pyautogui.click()
            elif blink_count == 2:
                pyautogui.hotkey('ctrl', '=')
            elif blink_count >= 3:
                pyautogui.hotkey('ctrl', '-')
        elif context == AppContext.CHROME:
            if blink_count == 1:
                pyautogui.click()
            elif blink_count == 2:
                pyautogui.doubleClick()
            elif blink_count >= 3:
                pyautogui.click(button='right')
        elif context == AppContext.YOUTUBE:
            if blink_count == 1:
                pyautogui.click()
            elif blink_count == 2:
                pyautogui.press('space')
            elif blink_count >= 3:
                pyautogui.press('m')
        elif context == AppContext.EXPLORER:
            if blink_count == 1:
                pyautogui.click()
            elif blink_count == 2:
                pyautogui.doubleClick()
            elif blink_count >= 3:
                pyautogui.hotkey('alt', 'up')
        elif context == AppContext.VSCODE:
            if blink_count == 1:
                pyautogui.click()
            elif blink_count == 2:
                pyautogui.doubleClick()
            elif blink_count >= 3:
                pyautogui.hotkey('ctrl', 's')
        elif context == AppContext.WORD:
            if blink_count == 1:
                pyautogui.click()
            elif blink_count == 2:
                pyautogui.doubleClick()
            elif blink_count >= 3:
                pyautogui.hotkey('ctrl', 's')
        elif context == AppContext.EXCEL:
            if blink_count == 1:
                pyautogui.click()
            elif blink_count == 2:
                pyautogui.doubleClick()
            elif blink_count >= 3:
                pyautogui.press('enter')
        elif context == AppContext.POWERPOINT:
            if blink_count == 1:
                pyautogui.click()
            elif blink_count == 2:
                pyautogui.doubleClick()
            elif blink_count >= 3:
                pyautogui.press('f5')
        elif context == AppContext.NOTEPAD:
            if blink_count == 1:
                pyautogui.click()
            elif blink_count == 2:
                pyautogui.doubleClick()
            elif blink_count >= 3:
                pyautogui.hotkey('ctrl', 's')
        elif context == AppContext.SPOTIFY:
            if blink_count == 1:
                pyautogui.click()
            elif blink_count == 2:
                pyautogui.doubleClick()
            elif blink_count >= 3:
                pyautogui.press('space')
        elif context == AppContext.ZOOM:
            if blink_count == 1:
                pyautogui.click()
            elif blink_count == 2:
                pyautogui.doubleClick()
            elif blink_count >= 3:
                pyautogui.hotkey('alt', 'a')
        elif context == AppContext.TEAMS:
            if blink_count == 1:
                pyautogui.click()
            elif blink_count == 2:
                pyautogui.doubleClick()
            elif blink_count >= 3:
                pyautogui.hotkey('ctrl', 'shift', 'm')
        else:  # Desktop default
            if blink_count == 1:
                pyautogui.click()
            elif blink_count == 2:
                pyautogui.doubleClick()
            elif blink_count >= 3:
                pyautogui.click(button='right')

        if blink_count == 1:
            self.last_action_label = "Left Click"
        elif blink_count == 2:
            if context == AppContext.PDF:
                self.last_action_label = "Zoom In"
            elif context == AppContext.YOUTUBE:
                self.last_action_label = "Play/Pause"
            else:
                self.last_action_label = "Double Click"
        elif blink_count >= 3:
            self.last_action_label = triple_labels.get(context, "Right Click")

    def execute_head_tilt_action(
        self,
        context: AppContext,
        tilt_direction: str,
        last_action_time: float,
    ) -> float:
        now = time.time()
        if now - last_action_time < config.ACTION_COOLDOWN:
            return last_action_time

        tilt_labels = {
            AppContext.CHROME: ("Next Tab", "Prev Tab"),
            AppContext.VSCODE: ("Next Tab", "Prev Tab"),
            AppContext.EXCEL: ("Next Sheet", "Prev Sheet"),
            AppContext.POWERPOINT: ("Next Slide", "Prev Slide"),
            AppContext.SPOTIFY: ("Next Track", "Prev Track"),
            AppContext.YOUTUBE: ("Forward 10s", "Rewind 10s"),
        }

        if context == AppContext.CHROME:
            if tilt_direction == "right":
                pyautogui.hotkey('ctrl', 'tab')
            else:
                pyautogui.hotkey('ctrl', 'shift', 'tab')
        elif context == AppContext.VSCODE:
            if tilt_direction == "right":
                pyautogui.hotkey('ctrl', 'pagedown')
            else:
                pyautogui.hotkey('ctrl', 'pageup')
        elif context == AppContext.EXCEL:
            if tilt_direction == "right":
                pyautogui.hotkey('ctrl', 'pagedown')
            else:
                pyautogui.hotkey('ctrl', 'pageup')
        elif context == AppContext.POWERPOINT:
            if tilt_direction == "right":
                pyautogui.press('pagedown')
            else:
                pyautogui.press('pageup')
        elif context == AppContext.SPOTIFY:
            if tilt_direction == "right":
                pyautogui.hotkey('ctrl', 'right')
            else:
                pyautogui.hotkey('ctrl', 'left')
        elif context == AppContext.YOUTUBE:
            if tilt_direction == "right":
                pyautogui.press('l')
            else:
                pyautogui.press('j')

        labels = tilt_labels.get(context, ("Tilt Right", "Tilt Left"))
        self.last_action_label = labels[0] if tilt_direction == "right" else labels[1]

        return now
