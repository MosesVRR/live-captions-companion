# PyInstaller build configuration for Live Captions Companion.
# Build on Windows with the same Python version used for development (3.13).

from PyInstaller.utils.hooks import collect_all, collect_submodules

pywinauto_datas, pywinauto_binaries, pywinauto_hiddenimports = collect_all("pywinauto")
comtypes_datas, comtypes_binaries, comtypes_hiddenimports = collect_all("comtypes")
win32com_hiddenimports = collect_submodules("win32com")

datas = pywinauto_datas + comtypes_datas
binaries = pywinauto_binaries + comtypes_binaries
hiddenimports = (
    pywinauto_hiddenimports
    + comtypes_hiddenimports
    + win32com_hiddenimports
    + [
        "pythoncom",
        "pywintypes",
        "win32api",
        "win32con",
        "win32gui",
        "win32timezone",
        "comtypes.client",
        "comtypes.gen",
        "pywinauto.controls.uia_controls",
        "pywinauto.uia_defines",
    ]
)


a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tests", "pytest", "unittest"],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="LiveCaptionsCompanion",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="LiveCaptionsCompanion",
)
