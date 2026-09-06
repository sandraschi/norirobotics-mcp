# Build Log — norirobotics-mcp

## 2026-09-06 — MCPB v0.1.0 + Tauri NSIS 1.0.0 (rebuild: nori_vr, skills endpoint)

**Changes since 2026-09-04 build:** `nori_vr` tool (Unity/Overte/Godot/MuJoCo/Isaac via fleet, real GLB + bridge probe), `GET /api/skills` now returns `nori-a3-expert` + `homebot-expert`, README/HelpPage VR crossconnects clarified ("using other fleet repos"), RUF001 ignore for api.py skills content.

**MCPB (mcpb/pack.ps1):** `dist/norirobotics-mcp-v0.1.0.mcpb` 79.0 KB (was 72.6 KB), 26 files (was 25), shasum `3b6b33f7…`, includes `tool_vr.py` 10.3 KB + `api.py` 18.3 KB. Manifest schema passes. WARNING: Not signed (expected, no cert).

**NSIS (native/build.ps1, all 5 steps green):**
- `tsc --noEmit` 0, `vite build` 335.94 KB index + 576.44 KB vendor, 1635 modules, 6.19s
- PyInstaller 6.22.2, 56.5 MB backend, smoke-test `NORI_MCP_PORT=11999` 5s — PASSED
- Tauri `cargo build --release` 2m 04s (incremental; only backend.rs/main.rs/config changed), `makensis` OK
- `native/target/release/bundle/nsis/Nori Robotics MCP_1.0.0_x64-setup.exe` 61.35 MB → `dist/norirobotics-mcp-1.0.0-setup.exe` (61.35 MB) + product-name copy
- `dist/norirobotics-mcp-backend.exe` 59.28 MB, no `pyi-crash.log`
- No regressions: `ruff` 0, `ruff format` 0, `pytest 51/51`, `tsc` 0, `biome ci` 0

**Ship:**
- `dist/norirobotics-mcp-1.0.0-setup.exe` (NSIS, currentUser) + `dist/norirobotics-mcp-v0.1.0.mcpb`
- `gh release upload v1.0.0 dist/norirobotics-mcp-1.0.0-setup.exe dist/norirobotics-mcp-v0.1.0.mcpb --clobber` (when tag cut)

## 2026-09-04 — Tauri NSIS 1.0.0

**Phase 1 audit (TAURI_PRODUCTION_PITFALLS.md A-J):**
- A Ports: 11970/11971 adjacent, WEBAPP_PORTS.md, `BACKEND_PORT=11970` matches `VITE_API_BASE`
- B Frontend: `API_BASE` absolute `http://127.0.0.1:11970` in prod, `tauri.conf.json` `csp` now explicit `connect-src http://127.0.0.1:11970`, `manualChunks` (react/vendor) + `VITE_API_BASE` define added, `frontendDist` `../web_sota/dist` correct (not `../dist`)
- C CORS: `allow_origins` includes `tauri.localhost`, `allow_origin_regex` covers `*.ts.net`
- D run_server.py: added eager `_strptime`/`_datetime`/`mcp.types`/`joserfc`, frozen `_MEIPASS` path, `sys.argv=["run_server.py","--serve"]`
- E Spec: `upx=False`, `noarchive=True`, `hiddenimports` added `cachetools`/`key_value`/`mcp.types`/`joserfc`/`pydantic` submodules, `collect_all` for `av`/`aiortc`/`cachetools`/`key_value`, `dist-info` keep for `mcp-`/`opentelemetry`/`fastmcp-`/`fastapi-`/`pydantic-`
- F backend.rs: `Stdio::null()` (was `piped` — deadlock), `free_port` multi-layer, `resolve_bundled_backend` prefers `resources/`, `BACKEND_PORT=11970`, `NORI_MCP_TAURI=1` + `NORI_MCP_HOST/PORT` env
- G main.rs: `Exit | ExitRequested` both kill + `wait()`, `setup` spawns backend async, devtools in debug
- H build.ps1: 5 steps, `API_BASE` port check, `tsc --noEmit` gate, fastmcp patch, venv `pyinstaller.exe`, pre-clean, 5 MB gate, smoke-test `NORI_MCP_PORT=11999` 5s, embed to `resources/` + `binaries/`, `tauri build --bundles nsis`, clean stray `target/release/*-backend.exe`
- I hooks.nsh: `KillProcessCurrentUser` for both `*-backend.exe` + `*-native.exe`, `installerHooks` wired, `installMode currentUser`, `webviewInstallMode skip`
- J stdio: `NORI_MCP_TAURI=1` disables stdio hijack, `isatty` shim

**Build (native/build.ps1):**
- `tsc --noEmit` 0, `vite build` 335 KB index + 576 KB vendor (code-split), `dist/index.html` has `modulepreload` for react/vendor
- PyInstaller 6.22.2, 56.5 MB `dist/norirobotics-mcp-backend.exe`, smoke-test `NORI_MCP_PORT=11999` 5s — PASSED (no `cachetools`/`isatty`/`_strptime` crash)
- Tauri `cargo build --release` 3m 02s, `norirobotics-mcp-native.exe` + `resources/norirobotics-mcp-backend.exe`
- NSIS: `native/target/release/bundle/nsis/Nori Robotics MCP_1.0.0_x64-setup.exe` 61.3 MB, copied to `dist/norirobotics-mcp-1.0.0-setup.exe` (61.3 MB) + product-name copy

**Verify:**
- `dist/norirobotics-mcp-backend.exe` 59.3 MB, `dist/*.mcpb` 72.6 KB, no `pyi-crash.log`
- Frontend `dist/` is `web_sota/dist` (not repo `dist`), so Tauri did not bundle backend/mcpb/nsis recursively — binary is 12 MB Rust + 61 MB NSIS, not 600 MB
- No regressions: `ruff` 0, `pyright` 0, `pytest 51/51`, `tsc` 0, `biome ci` 0

**Ship:**
- `dist/norirobotics-mcp-1.0.0-setup.exe` (NSIS, currentUser) + `dist/norirobotics-mcp-v0.1.0.mcpb`
- `gh release upload v1.0.0 dist/norirobotics-mcp-1.0.0-setup.exe dist/norirobotics-mcp-v0.1.0.mcpb --clobber` (when tag cut)
