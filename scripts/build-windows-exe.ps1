[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $Python)) {
    throw 'Virtual environment not found. Run scripts\setup-windows.ps1 first.'
}

Push-Location $ProjectRoot
try {
    & $Python -m pip install --upgrade pyinstaller
    & $Python -m PyInstaller `
        --noconfirm `
        --clean `
        --windowed `
        --onedir `
        --name Charlie `
        --paths . `
        --collect-submodules cli `
        --collect-submodules core `
        --collect-submodules features `
        --collect-submodules models `
        --collect-submodules ui `
        --collect-all tkinterdnd2 `
        --hidden-import tkinter `
        --hidden-import tkinter.ttk `
        --hidden-import PIL.ImageGrab `
        --add-data "config.example.json;." `
        main.py

    Write-Host "Built: $ProjectRoot\dist\Charlie\Charlie.exe" -ForegroundColor Green
    Write-Host 'On first launch, attach models and enter your local profile.' -ForegroundColor Green
}
finally {
    Pop-Location
}
