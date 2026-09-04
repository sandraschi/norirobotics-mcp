# Build Log — norirobotics-mcp

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
