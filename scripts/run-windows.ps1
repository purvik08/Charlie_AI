[CmdletBinding()]
param(
    [ValidateSet('GUI', 'CLI')]
    [string]$Mode = 'GUI',
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CommandArgs
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $Python)) {
    throw 'Virtual environment not found. Run scripts\setup-windows.ps1 first.'
}

Push-Location $ProjectRoot
try {
    if ($Mode -eq 'GUI') {
        & $Python main.py
    }
    else {
        & $Python -m cli.main @CommandArgs
    }
}
finally {
    Pop-Location
}
