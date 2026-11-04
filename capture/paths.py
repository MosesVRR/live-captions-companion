"""Application paths for persistent user data."""

import os
import shutil
from pathlib import Path

APP_DIRECTORY_NAME = "LiveCaptionsCompanion"
LEGACY_APP_DIRECTORY_NAME = "WindowsCaptionCapture"


def get_app_data_dir() -> Path:
    """Return the per-user application data directory.

    Windows: %LOCALAPPDATA%\\LiveCaptionsCompanion
    Other platforms: $XDG_DATA_HOME/live-captions-companion or ~/.local/share/...
    """
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if base:
            return Path(base) / APP_DIRECTORY_NAME
        return Path.home() / "AppData" / "Local" / APP_DIRECTORY_NAME

    base = os.environ.get("XDG_DATA_HOME")
    if base:
        return Path(base) / "live-captions-companion"
    return Path.home() / ".local" / "share" / "live-captions-companion"


def get_transcripts_dir() -> Path:
    """Return the transcript directory, migrating data from previous locations.

    Existing data is copied, not moved, so the old recordings remain intact
    until the user has verified the new location.
    """
    destination = get_app_data_dir() / "transcripts"

    # Migrate from the previous per-user application data directory.
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        old_app_dir = (
            Path(base) / LEGACY_APP_DIRECTORY_NAME
            if base
            else Path.home() / "AppData" / "Local" / LEGACY_APP_DIRECTORY_NAME
        )
    else:
        base = os.environ.get("XDG_DATA_HOME")
        old_app_dir = (
            Path(base) / "windows-caption-capture"
            if base
            else Path.home() / ".local" / "share" / "windows-caption-capture"
        )

    old_transcripts = old_app_dir / "transcripts"
    legacy_project_transcripts = Path.cwd() / "transcripts"

    for source in (old_transcripts, legacy_project_transcripts):
        if not destination.exists() and source.is_dir():
            try:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(source, destination)
            except OSError:
                # Fall back to the existing data rather than hiding it.
                return source

    return destination
