# Serve a delivery/example package over local HTTP (the page cannot run from file://).
param(
    [int]$Port = 8766,
    [string]$Dir = "delivery\materials_kg_final"
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
if (-not (Test-Path (Join-Path $Dir "index.html"))) {
    Write-Error "index.html not found under $Dir; unzip materials_kg_v3.1-delivery.zip first."
}
Write-Host "serving $Dir at http://127.0.0.1:$Port/"
python -m http.server $Port --bind 127.0.0.1 --directory $Dir
