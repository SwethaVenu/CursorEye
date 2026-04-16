"""Shared landmark utility functions and application context detection."""

from typing import Tuple

import numpy as np
import pygetwindow as gw

from .enums import AppContext


def dist(a, b) -> float:
    """Euclidean distance between two landmarks."""
    return np.linalg.norm(np.array([a.x, a.y]) - np.array([b.x, b.y]))


def get_ear(lm) -> Tuple[float, float, float]:
    """Eye Aspect Ratio — returns (left, right, average)."""
    left_ear = dist(lm[159], lm[145]) / max(dist(lm[33], lm[133]), 0.001)
    right_ear = dist(lm[386], lm[374]) / max(dist(lm[362], lm[263]), 0.001)
    return left_ear, right_ear, (left_ear + right_ear) / 2


def get_mar(lm) -> float:
    """Mouth Aspect Ratio."""
    vertical = dist(lm[13], lm[14])
    horizontal = dist(lm[78], lm[308])
    return vertical / max(horizontal, 0.001)


def get_context() -> AppContext:
    """Detect the active application context from the foreground window title."""
    try:
        window = gw.getActiveWindow()
        if not window:
            return AppContext.DESKTOP
        title = window.title.lower()

        if "youtube" in title:
            return AppContext.YOUTUBE
        if any(x in title for x in ["pdf", "acrobat", "reader", "foxit"]):
            return AppContext.PDF
        if any(x in title for x in ["chrome", "firefox", "edge", "brave", "opera", "safari"]):
            return AppContext.CHROME
        if "word" in title or ".docx" in title or ".doc" in title:
            return AppContext.WORD
        if "excel" in title or ".xlsx" in title or ".xls" in title:
            return AppContext.EXCEL
        if "powerpoint" in title or ".pptx" in title or ".ppt" in title:
            return AppContext.POWERPOINT
        if any(x in title for x in ["visual studio code", "vscode", "code -"]):
            return AppContext.VSCODE
        if "file explorer" in title or "explorer" in title:
            return AppContext.EXPLORER
        if "notepad" in title or ".txt" in title:
            return AppContext.NOTEPAD
        if "spotify" in title:
            return AppContext.SPOTIFY
        if "zoom" in title:
            return AppContext.ZOOM
        if "teams" in title or "microsoft teams" in title:
            return AppContext.TEAMS
        return AppContext.DESKTOP
    except Exception:
        return AppContext.DESKTOP
