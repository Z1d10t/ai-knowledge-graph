# Run the pytest suite from a checkout, with src/ on PYTHONPATH.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$env:PYTHONPATH = "$root\src"
$env:PYTHONIOENCODING = "utf-8"
python -m pytest tests -q @args
exit $LASTEXITCODE
