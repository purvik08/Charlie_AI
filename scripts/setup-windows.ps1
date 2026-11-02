[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Get-Command py -ErrorAction SilentlyContinue

if (-not $Python) {
    throw 'Python Launcher (py.exe) was not found. Install Python 3.10 or newer from python.org, then run this script again.'
}

Push-Location $ProjectRoot
try {
    & py -3 --version
    if ($LASTEXITCODE -ne 0) {
        throw 'A Python 3 interpreter was not found. Install Python 3.10 or newer, then run this script again.'
    }
    & py -3 -m venv .venv
    & .\.venv\Scripts\python.exe -m pip install --upgrade pip
    & .\.venv\Scripts\python.exe -m pip install -r requirements.txt

    if (-not (Test-Path config.json)) {
        Copy-Item config.example.json config.json
        Write-Host 'Created config.json from config.example.json.' -ForegroundColor Green
    }

    if (-not (Test-Path models)) {
        New-Item -ItemType Directory -Path models | Out-Null
    }

    Write-Host 'Charlie is ready. Start the desktop app with scripts\run-windows.ps1.' -ForegroundColor Green
}
finally {
    Pop-Location
}
