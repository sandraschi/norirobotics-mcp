#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Build PyInstaller sidecar for Tauri (norirobotics-mcp HTTP backend on :11970).
#>
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "=== norirobotics-mcp sidecar build ===" -ForegroundColor Cyan

Push-Location $Root
try {
    $pyiExe = "$Root\.venv\Scripts\pyinstaller.exe"
    if (-not (Test-Path $pyiExe)) {
        Write-Host "-> Installing PyInstaller in project venv..." -ForegroundColor Yellow
        uv add --dev pyinstaller
        $pyiExe = "$Root\.venv\Scripts\pyinstaller.exe"
    }
    $ver = & $pyiExe --version 2>&1
    Write-Host "-> PyInstaller: $ver ($pyiExe)" -ForegroundColor Gray

    Remove-Item -Recurse -Force "$Root\build\norirobotics-mcp-backend" -ErrorAction SilentlyContinue
    Remove-Item -Force "$Root\dist\norirobotics-mcp-backend.exe" -ErrorAction SilentlyContinue

    Write-Host "-> Running PyInstaller (may take several minutes)..." -ForegroundColor Yellow
    & $pyiExe "norirobotics-mcp-backend.spec" --clean --noconfirm
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed (exit $LASTEXITCODE)" }

    $triple = "x86_64-pc-windows-msvc"
    $src = "$Root\dist\norirobotics-mcp-backend.exe"
    $dstDir = "$Root\native\binaries"
    $dst = "$dstDir\norirobotics-mcp-backend-$triple.exe"

    if (-not (Test-Path $src)) { throw "Build output not found: $src" }
    $sizeMB = [math]::Round((Get-Item $src).Length / 1MB, 1)
    if ($sizeMB -lt 5) { throw "Backend exe is only $sizeMB MB at $src - PyInstaller produced a broken binary" }

    New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
    Copy-Item $src $dst -Force

    Write-Host "=== Sidecar ready ===" -ForegroundColor Green
    Write-Host "  $dst ($sizeMB MB)" -ForegroundColor Cyan
} finally {
    Pop-Location
}
