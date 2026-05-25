$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Port = if ($env:APP_PORT) { $env:APP_PORT } else { "8810" }
$HostAddress = if ($env:APP_HOST) { $env:APP_HOST } else { "127.0.0.1" }

if (-not (Test-Path $VenvPython)) {
    throw "Virtual environment not found. Run scripts\install_windows.ps1 first."
}

Push-Location (Join-Path $ProjectRoot "backend")
try {
    & $VenvPython manage.py migrate --noinput
    & $VenvPython manage.py seed_demo_data --load-samples
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

Push-Location (Join-Path $ProjectRoot "backend")
try {
    & $VenvPython manage.py runserver "$($HostAddress):$($Port)"
}
finally {
    Pop-Location
}
