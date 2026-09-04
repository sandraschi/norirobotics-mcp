import sys, os
site_pkgs = os.path.abspath('.venv/Lib/site-packages')
if site_pkgs not in sys.path:
    sys.path.insert(0, site_pkgs)
# -*- mode: python ; coding: utf-8 -*-
# Tauri sidecar — HTTP backend on port 11970 (Nori A3 control + session/recording tools).
from PyInstaller.utils.hooks import collect_all, collect_submodules, copy_metadata

datas = [("src/norirobotics_mcp", "norirobotics_mcp")]
for pkg in ("fastmcp", "fastapi", "uvicorn", "pydantic", "starlette", "httpx", "websockets", "mcp", "opentelemetry-api"):
    try:
        datas += copy_metadata(pkg)
    except Exception:
        pass

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
    "norirobotics_mcp.robot_profiles",
    "_strptime",
    "_datetime",
    "cachetools",
    "key_value",
    "mcp.types",
    "joserfc",
    "joserfc.jwk",
    "joserfc.jwt",
    "pydantic.networks",
    "pydantic.color",
    "pydantic.deprecated",
    "beartype",
    "sqlite3",
]

# Collect all pydantic submodules (lazy imports)
try:
    _pydantic_all = collect_submodules('pydantic')
    hiddenimports += _pydantic_all
except Exception:
    pass

# FastMCP 3.4+ needs cachetools/key_value
try:
    _cache_datas, _cache_binaries, _cache_hidden = collect_all("cachetools")
    datas += _cache_datas
    binaries += _cache_binaries
    hiddenimports += _cache_hidden
except Exception:
    pass

try:
    _kv_datas, _kv_binaries, _kv_hidden = collect_all("key_value")
    datas += _kv_datas
    binaries += _kv_binaries
    hiddenimports += _kv_hidden
except Exception:
    pass

# nori-sdk[all] pulls in aiortc (WebRTC) + av (PyAV/FFmpeg). Both are historically
# difficult for PyInstaller to freeze correctly: PyAV bundles compiled shared
# libraries that static analysis can miss, and aiortc has several C-extension
# dependencies (aioice, pylibsrtp, cryptography). collect_all() pulls in their
# datas/binaries/hiddenimports so PyInstaller doesn't silently drop them.
# UNVERIFIED until a real PyInstaller freeze + smoke test is run — see build.ps1
# Step 2's frozen-binary smoke test, which is the actual gate for this.
try:
    av_datas, av_binaries, av_hidden = collect_all("av")
    datas += av_datas
    binaries += av_binaries
    hiddenimports += av_hidden
except Exception:
    pass
try:
    aiortc_datas, aiortc_binaries, aiortc_hidden = collect_all("aiortc")
    datas += aiortc_datas
    binaries += aiortc_binaries
    hiddenimports += aiortc_hidden
except Exception:
    pass

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

# Keep essential dist-info for packages that call importlib.metadata.version at runtime
_keep_dist = ['mcp-', 'opentelemetry', 'fastmcp-', 'fastapi-', 'pydantic-']
_saved = [e for e in a.datas if isinstance(e, tuple) and any(k in str(e[0]) for k in _keep_dist) and '.dist-info' in str(e[0])]
for _list in [a.datas, a.binaries, a.zipfiles, a.scripts]:
    _list[:] = [e for e in _list if not (isinstance(e, tuple) and '.dist-info' in str(e[0]) and not any(k in str(e[0]) for k in _keep_dist))]
a.datas.extend(_saved)

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
