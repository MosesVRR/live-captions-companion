# Live Captions Companion

**Your Windows Live Captions, saved.**

Live Captions Companion is an independent Windows desktop companion for **Windows Live Captions**. It captures caption text exposed through Windows UI Automation and helps you save, search, review, edit, and export caption sessions.

> Live Captions Companion is an independent project. It is not affiliated with, endorsed by, or supported by Microsoft.

## Features

- Capture text exposed by Windows Live Captions into separate sessions.
- View, search, rename, edit, and delete saved sessions.
- Keep clean and timestamped transcript files, along with caption snapshots.
- Recover sessions left in a recording state after an unexpected shutdown.
- Export transcripts as TXT, Markdown, JSON, and SRT.
- Choose an export destination using the file dialog.

## Requirements

- Windows 10 or Windows 11 with Windows Live Captions available.
- Windows Live Captions must be running when you start a capture.

For development, Python 3.13 is recommended. End users do not need to install Python when using the packaged Windows build.

## Install and run (Windows)

1. Open the project's **Releases** page on GitHub.
2. Download the Windows application ZIP attached to the release.
3. Extract the entire ZIP folder to a location where you want to keep the application.
4. Open the extracted `LiveCaptionsCompanion` folder.
5. Run `LiveCaptionsCompanion.exe`.
6. Open Windows Live Captions before starting a recording in Live Captions Companion.

Keep the extracted folder together. The application is built with PyInstaller in one-folder mode, so the EXE depends on the other files and folders included beside it. Do not distribute or move only the EXE.

## Using the application

1. Start Windows Live Captions.
2. Launch Live Captions Companion.
3. Create or select a session in the application.
4. Start capturing while Windows Live Captions is displaying captions.
5. Stop the capture when finished. The session is saved and can be reopened for review.
6. Select a session to search, edit, or export its transcript.

The exact text captured depends on the caption content Windows exposes through its UI Automation interface.

## Where recordings are stored

By default, recordings are stored in the current user's local application data directory:

```text
%LOCALAPPDATA%\LiveCaptionsCompanion\transcripts
```

On first launch after upgrading from the previous application identity, existing recordings in `%LOCALAPPDATA%\WindowsCaptionCapture\transcripts` are copied to the new location. The original folder is left untouched. The application also supports migration from the older project-local `transcripts` folder.

The application does not upload transcripts. Exports are written to the destination selected by the user. Transcripts may contain private or sensitive information; obtain any required consent before capturing, exporting, or sharing them.

## Build from source

Build the Windows application on Windows. PyInstaller does not produce a Windows executable when run on Linux or macOS.

### Development setup

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

### Create the packaged application

From the project root, run the Windows build script in PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\build_windows.ps1
```

The execution-policy command applies only to the current PowerShell process. If your system is managed by an organization, follow its script-execution policy instead.

The script installs the build dependencies, runs the unit tests, and creates the distributable application folder at:

```text
dist\LiveCaptionsCompanion\
```

Distribute the entire `LiveCaptionsCompanion` folder, for example by compressing it into a ZIP file. The packaged folder has been tested on a separate Windows machine where Python was not installed.

## Known limitations

- Captured text depends on what Windows Live Captions exposes through Windows UI Automation.
- Sentence timestamps represent when a completed sentence was detected, not precise word-level speech timing.
- SRT subtitle timing is approximate and may need adjustment.
- Speaker identification is not currently implemented.

## License

Live Captions Companion is released under the [MIT License](LICENSE).

## Third-party software

This application uses third-party Python packages and Qt/PySide components. Those dependencies remain subject to their respective licenses and terms. Refer to the package documentation and license notices for details.
