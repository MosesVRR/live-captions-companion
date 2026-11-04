"""Export captured sessions to portable transcript formats."""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

TIMESTAMP_PATTERN = re.compile(r"^\[(\d{2}:\d{2}:\d{2})\]\s+(.*)$")


def read_timestamped_sentences(path: str | Path) -> list[dict[str, str]]:
    """Read [HH:MM:SS] sentence records from a timestamped transcript."""
    records: list[dict[str, str]] = []
    source = Path(path)
    if not source.is_file():
        return records
    for line in source.read_text(encoding="utf-8").splitlines():
        match = TIMESTAMP_PATTERN.match(line.strip())
        if match:
            records.append({"time": match.group(1), "text": match.group(2)})
    return records


def _seconds_from_clock(value: str, start_clock: str) -> int:
    """Convert a time-of-day timestamp to seconds since the session start."""
    stamp = datetime.strptime(value, "%H:%M:%S")
    start = datetime.strptime(start_clock, "%H:%M:%S")
    seconds = int((stamp - start).total_seconds())
    if seconds < 0:
        seconds += 24 * 60 * 60
    return seconds


def _srt_time(seconds: int) -> str:
    seconds = max(0, seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02},000"


def export_session(
    destination: str | Path,
    file_format: str,
    transcript: str,
    metadata: dict[str, Any],
    timestamped_transcript_path: str | Path | None = None,
) -> Path:
    """Export transcript content without modifying the original session."""
    destination = Path(destination)
    file_format = file_format.lower().lstrip(".")
    if file_format not in {"txt", "md", "json", "srt"}:
        raise ValueError(f"Unsupported export format: {file_format}")

    records = (
        read_timestamped_sentences(timestamped_transcript_path)
        if timestamped_transcript_path
        else []
    )
    session_metadata = {
        key: value for key, value in metadata.items() if not key.startswith("_")
    }

    if file_format == "txt":
        content = transcript
    elif file_format == "md":
        title = metadata.get("name") or metadata.get("session_id") or "Caption transcript"
        lines = [f"# {title}", ""]
        if metadata.get("started_at"):
            lines.append(f"- **Started:** {metadata['started_at']}")
        if metadata.get("ended_at"):
            lines.append(f"- **Ended:** {metadata['ended_at']}")
        if metadata.get("duration_seconds") is not None:
            lines.append(f"- **Duration:** {metadata['duration_seconds']} seconds")
        if metadata.get("status"):
            lines.append(f"- **Status:** {metadata['status']}")
        lines.extend(["", "## Transcript", "", transcript.strip(), ""])
        if records:
            lines.extend(["## Timestamped sentences", ""])
            lines.extend(f"- `{record['time']}` — {record['text']}" for record in records)
            lines.append("")
        content = "\n".join(lines)
    elif file_format == "json":
        payload = {
            "session": session_metadata,
            "transcript": transcript,
            "timestamped_sentences": records,
            "timestamp_note": (
                "Times indicate when a completed sentence was detected by the capture worker; "
                "they are not precise word-level speech timings."
            ),
        }
        content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    else:
        if not records:
            raise ValueError(
                "No timestamped sentences are available for this session. "
                "Record a session with completed sentences before exporting SRT."
            )
        started_at = metadata.get("started_at")
        if not started_at:
            raise ValueError("Session start time is unavailable; cannot create SRT timings.")
        start_clock = datetime.fromisoformat(started_at).strftime("%H:%M:%S")
        start_seconds = [
            _seconds_from_clock(record["time"], start_clock) for record in records
        ]
        cues = []
        for index, record in enumerate(records):
            cue_start = start_seconds[index]
            if index + 1 < len(start_seconds):
                cue_end = max(cue_start + 1, start_seconds[index + 1])
            else:
                cue_end = cue_start + 3
            cues.append(
                f"{index + 1}\n{_srt_time(cue_start)} --> {_srt_time(cue_end)}\n{record['text']}"
            )
        content = "\n\n".join(cues) + "\n"

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    return destination
