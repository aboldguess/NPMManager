# Install.ps1 - Setup script for NPMManager
# This PowerShell script checks for required dependencies and installs
# Python packages listed in requirements.txt.
#
# Run this script from PowerShell on Windows.

# Function to check if a command exists in the current PATH
function Test-Command {
    param(
        [string]$Command
    )
    return [bool](Get-Command $Command -ErrorAction SilentlyContinue)
}

Write-Host "== Checking system dependencies =="

# Ensure Python is available
if (-not (Test-Command 'python')) {
    Write-Host "Python 3.x is required. Please install it from https://www.python.org/downloads/"
    exit 1
}

# Display detected Python version
$pythonVersion = python --version 2>&1
Write-Host "Found $pythonVersion"

# Ensure pip is available; attempt bootstrap if missing
if (-not (Test-Command 'pip')) {
    Write-Host "pip not found; attempting to install using 'python -m ensurepip'"
    python -m ensurepip --upgrade
}

# Ensure Node.js is installed
if (-not (Test-Command 'node')) {
    Write-Host "Node.js is required. Please install it from https://nodejs.org/"
    exit 1
}

# Ensure git is installed
if (-not (Test-Command 'git')) {
    Write-Host "Git is required. Please install it from https://git-scm.com/download/win"
    exit 1
}

# Upgrade pip and install Python dependencies
Write-Host "== Installing Python packages =="
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Write-Host "All dependencies are installed. You can now run 'python manager.py'"
