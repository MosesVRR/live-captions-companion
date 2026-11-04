# Windows Caption Capture

A Windows desktop utility that captures text exposed by Windows Live Captions and saves each capture as a local session.

## Features

- Capture Windows Live Captions into separate sessions.
- View, search, rename, edit, and delete saved sessions.
- Preserve clean and timestamped transcript files, plus caption snapshots.
- Detect sessions left in a recording state after an unexpected shutdown.
- Export transcripts as TXT, Markdown, JSON, and SRT.

## Requirements

- Windows 10 or Windows 11 with Windows Live Captions available.
- Python 3.12 or 3.13 is recommended for development until the full UI Automation dependency stack is verified on newer Python versions.
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

Run the tests:

```powershell
python -m unittest discover -s tests -v
```

## Where recordings are stored

By default, recordings are stored in the current user's local application data directory:

```text
%LOCALAPPDATA%\WindowsCaptionCapture\transcripts
```

The application does not upload transcripts. Exports are written to the destination selected by the user. Treat captured transcripts as potentially sensitive and obtain any required consent before capturing or sharing them.

## Known limitations

- Captured text depends on what Windows Live Captions exposes through Windows UI Automation.
- Sentence timestamps represent when a completed sentence was detected, not precise word-level speech timing.
- SRT subtitle timing is therefore approximate and may need adjustment.
- Speaker identification is not currently implemented.

## Planned improvements

- More frequent durable writes during active recording.
- Additional recovery and interruption testing.
- Improved speaker and timing support, where Windows exposes suitable information.
- A packaged installer and Microsoft Store release, subject to compatibility testing and Store certification.

## Development status

This project is under active development. The current source is a prototype and has not yet been certified or released through the Microsoft Store.
