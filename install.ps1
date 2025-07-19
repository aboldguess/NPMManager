# Install.ps1 - Setup script for PM2 Frontend
# Checks that Python, Node.js, git and PM2 are available and installs
# Python packages listed in requirements.txt.

function Test-Command {
    param([string]$Command)
    return [bool](Get-Command $Command -ErrorAction SilentlyContinue)
}

Write-Host "== Checking system dependencies =="

if (-not (Test-Command 'python')) {
    Write-Host 'Python 3.x is required. Please install it from https://www.python.org/downloads/'
    exit 1
}

$pythonVersion = python --version 2>&1
Write-Host "Found $pythonVersion"

if (-not (Test-Command 'pip')) {
    Write-Host "pip not found; attempting bootstrap"
    python -m ensurepip --upgrade
}

if (-not (Test-Command 'node')) {
    Write-Host 'Node.js is required. Please install it from https://nodejs.org/'
    exit 1
}

if (-not (Test-Command 'git')) {
    Write-Host 'Git is required. Please install it from https://git-scm.com/download/win'
    exit 1
}

if (-not (Test-Command 'pm2')) {
    Write-Host 'PM2 is required. Install it with `npm install -g pm2`'
    exit 1
}

Write-Host "== Installing Python packages =="
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Write-Host "Setup complete. Run 'python manager.py' to start the GUI."
