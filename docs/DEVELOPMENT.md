# Development Setup

## Tools Required

```bash
# Windows (winget)
winget install astral-sh.uv
winget install Git.Git
winget install OpenJS.NodeJS
winget install Casey.Just

# Verify
uv --version
git --version
node --version
just --version
```

## Setup

```bash
git clone https://github.com/sandraschi/norirobotics-mcp
cd norirobotics-mcp
uv sync --extra dev
```

## Common Tasks

```bash
just lint      # ruff + biome
just test      # pytest (51 cases, run against the real nori_sdk mock — no network needed)
just fmt       # ruff format + fix
just ci        # sync + test + lint + pyright + tsc + biome (what CI runs)
just serve     # start the MCP server (HTTP, :11970)
```

## Working on tool code

Every op in `tool_control.py` / `tool_recording.py` / `tool_session.py` maps 1:1 onto a real
`nori_sdk.RemoteTeleop` method — before adding or changing an op, verify the method actually
exists on the installed package:

```bash
uv run python -c "from nori_sdk.mock import mock_session; import inspect; print([m for m in dir(mock_session) ])"
```

or read `.venv/Lib/site-packages/nori_sdk/` directly. Do not invent an op that isn't backed by
the SDK — see `AGENTS.md` for why.

## Code Standards
Link to mcp-central-docs standards: `mcp-central-docs/standards/TOOL_DESIGN_STANDARDS.md`.
