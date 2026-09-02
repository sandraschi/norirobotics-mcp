set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]

# --- Dashboard ---

default:
    @just --list

# --- Quality ---

lint:
    uv run ruff check .
    Set-Location '{{justfile_directory()}}\web_sota'; npx @biomejs/biome ci .

fix:
    uv run ruff check . --fix --unsafe-fixes
    uv run ruff format .
    Set-Location '{{justfile_directory()}}\web_sota'; npx @biomejs/biome check --write .

fmt:
    uv run ruff format .
    uv run ruff check --fix .

# --- norirobotics-mcp ---

serve:
    uv run python -m norirobotics_mcp --serve

stdio:
    uv run python -m norirobotics_mcp --stdio

test:
    uv run pytest -q

ci:
    uv sync --extra dev
    uv run pytest -q
    uv run ruff check .
    uv run ruff format --check .

mcpb-pack:
    pwsh -NoProfile -File '{{justfile_directory()}}\mcpb\pack.ps1'

# --- Native / Tauri (config scaffolded; actual build via nsis-build skill) ---

build-native:
    $env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
    Set-Location '{{justfile_directory()}}\native'
    pwsh -NoProfile -File '{{justfile_directory()}}\native\build.ps1'

bootstrap:
    uv sync --group dev
    Write-Host "norirobotics-mcp deps installed." -ForegroundColor Green
