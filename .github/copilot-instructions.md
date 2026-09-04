## Session Context (norirobotics-mcp)

You have access to the Nori Robotics A3 bimanual home robot MCP: specs/SDK/lineage tools, live control session management, motion/safety control, and LeRobot-format episode recording (real robot or a built-in mock when no credentials are configured).

**Before starting work:**
1. Get robot facts/specs (no session needed): `nori_info(operation="info")`
2. Open a control session: `nori_session(operation="connect")`
3. Check session/robot status: `nori_session(operation="status")`

**At end of work:**
- Close the session: `nori_session(operation="disconnect")` (or `nori_shutdown()`)
