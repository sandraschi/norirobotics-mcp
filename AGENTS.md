# norirobotics-mcp — Agent Guide

## Overview
FastMCP 3.4 MCP for the Nori Robotics A3 bimanual home robot — specs/SDK/lineage/community
knowledge, live session control via nori-sdk (WebRTC + Supabase), motion/safety, and
LeRobot-format episode recording. No physical unit exists in this household yet (Nori A3
ships Fall 2026) — every session-gated tool defaults to nori_sdk's own `mock_session()`.

## Entry Points

- `uv run norirobotics-mcp` → `norirobotics_mcp.__main__:main`
- `just serve` → HTTP transport on `:11970`, MCP at `/mcp`

## Standards
- FastMCP 3.4+ portmanteau tool pattern — tools use `operation` enum param
- Responses: structured dicts with `success`, `message`, domain-specific fields
- See [mcp-central-docs](https://github.com/sandraschi/mcp-central-docs) for fleet-wide coding standards

## Key Files
- `README.md` — full documentation
- `docs/ARCHITECTURE.md` — nori-sdk session model, mock-vs-real posture
- `src/norirobotics_mcp/knowledge.py` — static spec/lineage/community data (see
  `mcp-central-docs/projects/norirobotics-mcp/RESEARCH.md` for the sourced research pass)
- `src/norirobotics_mcp/session_state.py` — the one place mock-vs-real session choice happens
- `pyproject.toml` — build config and entry points

## Quick Ref

```powershell
uv run pytest tests/ -q
just ci
```

## Critical honesty note for future agents

Do not fabricate a local serial/ROS/REST API for the A3 — there isn't one. The only real
integration surface is `nori-sdk` (PyPI, Apache-2.0) over WebRTC + Supabase signaling. If you
add a tool, it must map onto a real `nori_sdk.RemoteTeleop` / `nori_sdk.mock.MockRobot` method
— verify against the installed package (`uv run python -c "import nori_sdk; help(nori_sdk)"`)
before writing docstrings that claim behavior.

Install docs: follow mcp-central-docs/standards/AGENT_INSTALL_REFERENCE.md
