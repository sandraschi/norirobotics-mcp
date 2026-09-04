import sys, os
site_pkgs = os.path.abspath('.venv/Lib/site-packages')
if site_pkgs not in sys.path:
    sys.path.insert(0, site_pkgs)
# -*- mode: python ; coding: utf-8 -*-
# Tauri sidecar — HTTP backend on port 11970 (Nori A3 control + session/recording tools).
from PyInstaller.utils.hooks import collect_all, copy_metadata

datas = [("src/norirobotics_mcp", "norirobotics_mcp")]
for pkg in ("fastmcp", "fastapi", "uvicorn", "pydantic", "starlette", "httpx", "websockets"):
    datas += copy_metadata(pkg)

binaries = []
hiddenimports = [
    "charset_normalizer",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.asyncio",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.httptools_impl",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "norirobotics_mcp.api",
    "norirobotics_mcp.server",
    "norirobotics_mcp.config",
    "norirobotics_mcp.lifecycle",
    "norirobotics_mcp.session_state",
    "norirobotics_mcp.tool_control",
    "norirobotics_mcp.tool_info",
    "norirobotics_mcp.tool_recording",
    "norirobotics_mcp.tool_session",
    "norirobotics_mcp.tools_manifest",
    "norirobotics_mcp.knowledge",
    "_strptime",
]

# nori-sdk[all] pulls in aiortc (WebRTC) + av (PyAV/FFmpeg). Both are historically
# difficult for PyInstaller to freeze correctly: PyAV bundles compiled shared
# libraries that static analysis can miss, and aiortc has several C-extension
# dependencies (aioice, pylibsrtp, cryptography). collect_all() pulls in their
# datas/binaries/hiddenimports so PyInstaller doesn't silently drop them.
# UNVERIFIED until a real PyInstaller freeze + smoke test is run — see build.ps1
# Step 2's frozen-binary smoke test, which is the actual gate for this.
av_datas, av_binaries, av_hidden = collect_all("av")
aiortc_datas, aiortc_binaries, aiortc_hidden = collect_all("aiortc")
datas += av_datas + aiortc_datas
binaries += av_binaries + aiortc_binaries
hiddenimports += av_hidden + aiortc_hidden

a = Analysis(
    ["run_server.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "lancedb",
        "sentence_transformers",
        "torch",
        "transformers",
    ],
    noarchive=True,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],

    name="norirobotics-mcp-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
