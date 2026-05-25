$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    $PythonCommand = Get-Command py -ErrorAction SilentlyContinue
    if ($PythonCommand) {
        & py -3.11 -m venv (Join-Path $ProjectRoot ".venv")
    }
    else {
        & python -m venv (Join-Path $ProjectRoot ".venv")
    }
}

& $VenvPython -m pip install -r (Join-Path $ProjectRoot "requirements.txt")

Push-Location (Join-Path $ProjectRoot "frontend")
try {
    npm install
}
finally {
    Pop-Location
}
