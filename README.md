# Live Captions Companion

An independent Windows desktop companion for **Windows Live Captions**. It captures
caption text exposed by Windows UI Automation and helps you save, search, review,
edit, and export caption sessions.

> Live Captions Companion is an independent project and is not affiliated with,
> endorsed by, or supported by Microsoft.

## Features

- Capture text exposed by Windows Live Captions into separate sessions.
- View, search, rename, edit, and delete saved sessions.
- Preserve clean and timestamped transcript files, plus caption snapshots.
- Detect sessions left in a recording state after an unexpected shutdown.
- Export transcripts as TXT, Markdown, JSON, and SRT.

## Requirements

- Windows 10 or Windows 11 with Windows Live Captions available.
- Python 3.12 or 3.13 is recommended for development while the UI Automation
  dependency stack is validated on newer Python versions.
- Windows Live Captions must be running when a capture is started.

## Development setup

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Run the application:

```powershell
python main.py
```

Run tests:

```powershell
python -m unittest discover -s tests -v
```

## Where recordings are stored

By default, recordings are stored in the current user's local application data
directory:

```text
%LOCALAPPDATA%\LiveCaptionsCompanion\transcripts
```

On first launch after upgrading from the previous application identity, existing
recordings in `%LOCALAPPDATA%\WindowsCaptionCapture\transcripts` are copied to
the new location. The original folder is left untouched. The application also
supports migration from the older project-local `transcripts` folder.

The application does not upload transcripts. Exports are written to the
destination selected by the user. Captured transcripts may contain sensitive
information; obtain any required consent before capturing or sharing them.

## Known limitations

- Captured text depends on what Windows Live Captions exposes through Windows UI
  Automation.
- Sentence timestamps represent when a completed sentence was detected, not
  precise word-level speech timing.
- SRT subtitle timing is approximate and may need adjustment.
- Speaker identification is not currently implemented.

## Planned improvements

- More frequent durable writes during active recording.
- Additional recovery and interruption testing.
- Improved speaker and timing support, where Windows exposes suitable information.
- A packaged installer and Microsoft Store release, subject to compatibility
  testing and Store certification.

## Project status

This project is under active development. It is not currently a Microsoft Store
release. Live Captions Companion is an independent companion utility, not an
official Microsoft application.
