"""Application paths for persistent user data."""

import os
import shutil
from pathlib import Path

APP_DIRECTORY_NAME = "WindowsCaptionCapture"


def get_app_data_dir() -> Path:
    """Return the per-user application data directory.

    Windows: %LOCALAPPDATA%\\WindowsCaptionCapture
    Other platforms: $XDG_DATA_HOME/windows-caption-capture or ~/.local/share/...
    """
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if base:
            return Path(base) / APP_DIRECTORY_NAME
        return Path.home() / "AppData" / "Local" / APP_DIRECTORY_NAME

    base = os.environ.get("XDG_DATA_HOME")
    if base:
        return Path(base) / "windows-caption-capture"
    return Path.home() / ".local" / "share" / "windows-caption-capture"


def get_transcripts_dir() -> Path:
    """Return the default transcript directory, migrating legacy local data once.

    Older development versions stored recordings in ./transcripts. If that
    folder exists and the new per-user location does not, copy it so existing
    sessions remain available after the update. The original is left untouched.
    """
    destination = get_app_data_dir() / "transcripts"
    legacy = Path.cwd() / "transcripts"

    if not destination.exists() and legacy.is_dir():
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(legacy, destination)
        except OSError:
            # Keep existing data accessible if migration cannot be completed.
            return legacy

    return destination
