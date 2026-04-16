"""Enumerations used across the Face Control System."""

from enum import Enum


class AppContext(Enum):
    DESKTOP = "desktop"
    PDF = "pdf"
    CHROME = "chrome"
    EXPLORER = "explorer"
    VSCODE = "vscode"
    WORD = "word"
    EXCEL = "excel"
    POWERPOINT = "powerpoint"
    NOTEPAD = "notepad"
    SPOTIFY = "spotify"
    YOUTUBE = "youtube"
    ZOOM = "zoom"
    TEAMS = "teams"


class ControlState(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    CALIBRATING = "calibrating"


class KeyboardState(Enum):
    HIDDEN = "hidden"
    ROW_SCANNING = "row_scanning"
    COLUMN_SCANNING = "column_scanning"
