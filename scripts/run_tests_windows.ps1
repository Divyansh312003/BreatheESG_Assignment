$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    throw "Virtual environment not found. Run scripts\install_windows.ps1 first."
}

Push-Location (Join-Path $ProjectRoot "backend")
try {
    & $VenvPython manage.py test
}
finally {
    Pop-Location
}

Push-Location (Join-Path $ProjectRoot "frontend")
try {
    npm run build
}
finally {
    Pop-Location
}
