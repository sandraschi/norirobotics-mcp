# Configuration

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NORI_MCP_HOST` | `127.0.0.1` | HTTP transport bind host |
| `NORI_MCP_PORT` | `11970` | HTTP transport bind port |
| `NORI_MCP_SUPABASE_URL` | *(unset)* | Supabase project URL for real-robot signaling. Unset = mock session. |
| `NORI_MCP_SUPABASE_ANON_KEY` | *(unset)* | Supabase anonymous key. |
| `NORI_MCP_ROBOT_ROOM` | *(unset)* | Robot identifier for Supabase signaling room, e.g. `NORI-A3-0001`. |
| `NORI_MCP_USER_EMAIL` | *(unset)* | Nori account email, for `UserAuth` token refresh. |
| `NORI_MCP_USER_PASSWORD` | *(unset)* | Nori account password. |
| `NORI_MCP_CONNECT_TIMEOUT_S` | `15.0` | Timeout for `nori_session(operation="wait_ready")`. |

All four of `NORI_MCP_SUPABASE_URL` / `NORI_MCP_SUPABASE_ANON_KEY` / `NORI_MCP_ROBOT_ROOM` must
be set for a real connection; if any is missing, `nori_session(operation="connect")` falls back
to `nori_sdk.mock.mock_session()`.

## Setting Variables

In `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "norirobotics-mcp": {
      "env": {
        "NORI_MCP_SUPABASE_URL": "https://xxxx.supabase.co",
        "NORI_MCP_SUPABASE_ANON_KEY": "...",
        "NORI_MCP_ROBOT_ROOM": "NORI-A3-0001"
      }
    }
  }
}
```

Or copy `.env.example` to `.env` when running from source.
