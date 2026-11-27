# Build and verify the two-paper example without any LLM call.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$env:PYTHONPATH = "$root\src;$root"
$env:PYTHONIOENCODING = "utf-8"

if (-not (Test-Path "examples\mini_v3\relations.jsonl")) {
    python scripts\build_mini_example.py
}

python article\export_materials_graph.py `
    --input-dir examples/mini_v3 `
    --papers-dir examples/mini_papers `
    --output-dir examples/mini_package `
    --version "v3.0-mini" `
    --force

python article\export_materials_graph.py --verify-only --output-dir examples/mini_package
exit $LASTEXITCODE
