$ErrorActionPreference = "Stop"

if (-not $IsWindows -and $env:OS -ne "Windows_NT") {
    throw "This build script must be run on Windows. PyInstaller builds are platform-specific."
}

$Python = "py"
$PythonVersion = "3.13"

Write-Host "Checking Python $PythonVersion..."
& $Python -$PythonVersion --version
if ($LASTEXITCODE -ne 0) {
    throw "Python $PythonVersion was not found. Install Python 3.13 and try again."
}

Write-Host "Installing application dependencies..."
& $Python -$PythonVersion -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Could not upgrade pip." }
& $Python -$PythonVersion -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Could not install application dependencies." }

Write-Host "Installing build dependencies..."
& $Python -$PythonVersion -m pip install -r build_requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Could not install build dependencies." }

Write-Host "Running unit tests..."
& $Python -$PythonVersion -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw "Unit tests failed; build cancelled." }

Write-Host "Building the application..."
& $Python -$PythonVersion -m PyInstaller --noconfirm --clean LiveCaptionsCompanion.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed." }

Write-Host "Build complete: dist\LiveCaptionsCompanion\LiveCaptionsCompanion.exe"
Write-Host "Test this folder on a Windows machine before distributing it."
