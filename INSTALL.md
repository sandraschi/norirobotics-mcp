# Installing norirobotics-mcp

## Prerequisites

| Tool | Purpose | Install |
|------|---------|---------|
| Claude Desktop | Required host | [download](https://claude.ai/download) |
| Git | Clone repo (Option C/D only) | `winget install Git.Git` |
| Python + uv | Run server (Option C/D only) | `winget install astral-sh.uv` |
| Node.js | mcpb CLI (Option B only) | `winget install OpenJS.NodeJS` |

> Windows: all installs via [winget](https://learn.microsoft.com/en-us/windows/package-manager/winget/)
> macOS: use `brew install` equivalents
> Linux: use your distro package manager

## Option A — Drag and Drop (Recommended)
1. Go to [Releases](https://github.com/sandraschi/norirobotics-mcp/releases/latest)
2. Download `norirobotics-mcp-{version}.mcpb`
3. Open Claude Desktop → drag the file onto the window
   *Or*: Settings → MCP Servers → Install from file

## Option B — mcpb CLI
```bash
# Requires Node.js (see Prerequisites)
npx @anthropic-ai/mcpb install https://github.com/sandraschi/norirobotics-mcp
```

## Option C — Manual Configuration
1. Clone: `git clone https://github.com/sandraschi/norirobotics-mcp`
2. Install deps: `cd norirobotics-mcp && uv sync`
3. Add to Claude Desktop config:

```json
{
  "mcpServers": {
    "norirobotics-mcp": {
      "command": "uv",
      "args": ["--directory", "C:\\path\\to\\norirobotics-mcp", "run", "norirobotics-mcp"],
      "env": { "PYTHONUNBUFFERED": "1" }
    }
  }
}
```

Config file location:
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

4. Restart Claude Desktop

## Option D — Developer Mode
For contributing or running from source with live reload.
See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## Verify Installation
After installing, open Claude Desktop and type:
> "What are the Nori A3's specs?"

You should see: a structured spec sheet (19 DOF, Feetech actuators, Pi 5, etc.) from
`nori_info(operation='specs')` — this works with zero configuration, no robot or credentials
needed.

To confirm the session/mock path also works:
> "Open a Nori session and show me the status."

You should see: `connected: true, mock: true` — nori-sdk's own mock robot, since no physical A3
exists yet (ships Fall 2026) and no Supabase credentials are configured.

## Troubleshooting
See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for common issues.
