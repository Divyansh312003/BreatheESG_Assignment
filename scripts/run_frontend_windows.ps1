$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

Push-Location (Join-Path $ProjectRoot "frontend")
try {
    npm run dev
}
finally {
    Pop-Location
}
