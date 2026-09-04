import { useState } from "react";
import { Card, CardTitle } from "@/components/ui/card";

type Tab = "about" | "quickstart" | "reference" | "faq";

const TABS: { id: Tab; label: string }[] = [
  { id: "about", label: "About Nori A3" },
  { id: "quickstart", label: "Quick start" },
  { id: "reference", label: "API & tools" },
  { id: "faq", label: "FAQ" },
];

const toolsList = [
  {
    name: "nori_info",
    op: "specs | sdk_links | predecessor | community | actuator_upgrade | fleet_peers",
    desc: "Static reference data, no session",
  },
  {
    name: "nori_session",
    op: "connect | disconnect | status | wait_ready",
    desc: "Session lifecycle",
  },
  {
    name: "nori_control",
    op: "jog | action | pose | estop | reset_*",
    desc: "Motion + safety, requires session",
  },
  {
    name: "nori_recording",
    op: "start | stop | snapshot | frames",
    desc: "LeRobot-format episode capture",
  },
];

const fleetPeers = [
  {
    id: "robotics-mcp",
    note: "Fleet hub for physical + virtual robots. norirobotics-mcp registers here as a member robot, bridged via HTTP rather than reimplemented.",
  },
  {
    id: "teleoperator-mcp",
    note: "WebXR teleop gateway (Pico 4 / Quest). Nori's own control path is WebRTC remote-teleop — a natural pairing for VR-driven demonstration collection.",
  },
  {
    id: "vla-mcp",
    note: "Logged as alpha/shelfware fleet-wide. Nori's LeRobot-format recordings are its first plausible real workload.",
  },
  {
    id: "universal-actuator-mcp",
    note: "Motor/actuator abstraction layer — future home for Feetech-to-QDD actuator-upgrade tooling.",
  },
  {
    id: "bumi-mcp",
    note: "Closest structural precedent: another wheeled consumer robot, specs+OSS-info tools shipped first, control gated behind a verified bridge second.",
  },
];

const vrCrossconnects = [
  {
    id: "resonite-mcp",
    note: "ResoniteLink WebSocket control. Fixture spawner + real-physics-bounce animate — stage a pick-and-place task in VR before running it on hardware. Uses nori_a3_posed.mesh.json via spawn_mesh.",
  },
  {
    id: "overte-mcp",
    note: "Open-source metaverse control — where the fixture-spawner/animate/depot pattern was first built and live-verified before porting to the others. You saw Overte live.",
  },
  {
    id: "unity3d-mcp",
    note: "Unity Editor automation via a live TCP bridge — robotics-mcp's primary virtual-robot spawn target, now real: nori_a3_posed.glb via model depot + spawn_fixture (not a box primitive).",
  },
  {
    id: "godot-mcp",
    note: "Godot 4 engine control via TCP bridge, plus a real model/texture asset depot with backup/restore. Same GLB as Unity.",
  },
  {
    id: "mujoco-mcp",
    note: "MuJoCo physics viewer — local mujoco.viewer.launch_passive from the same URDF (no fleet repo needed, this repo's models/nori_description/ is the source).",
  },
  {
    id: "isaac-mcp",
    note: "NVIDIA Isaac Sim (Omniverse) — USD import of nori_a3_posed.glb/URDF for sim2real physics twin.",
  },
  {
    id: "vrchat-mcp",
    note: "OSC avatar control + REST (friends, notifications, live Pipeline events) — plugs in at the social/telepresence layer, not object-spawning.",
  },
];

const faq = [
  {
    q: "When does Nori A3 ship?",
    a: "Fall 2026 — second batch, $1,688, no deposit, per norirobotics.com. No unit exists in this household yet.",
  },
  {
    q: "Why does everything say 'mock: true'?",
    a: "Because there's no real robot to connect to. nori_session(operation='connect') falls back to nori_sdk's own mock_session() unless NORI_MCP_SUPABASE_URL / NORI_MCP_SUPABASE_ANON_KEY / NORI_MCP_ROBOT_ROOM are all set — see Settings.",
  },
  {
    q: "Is there a local/serial API I can use instead of cloud WebRTC?",
    a: "No. nori-sdk's RemoteTeleop connects over a WebRTC data channel with Supabase Realtime signaling — that's the only documented transport. This was flagged as a privacy/telemetry concern on the Hacker News launch thread.",
  },
  {
    q: "What's the actuator-upgrade note about?",
    a: "Nori A3 uses Feetech STS-series RC-style bus servos. HN commenters suggested QDD actuators (CubeMars, MyActuator) as a precision upgrade path — see nori_info(operation='actuator_upgrade') for the full, sourced note. No specific part-number recommendation is made; it needs a real torque comparison pass first.",
  },
];

export function HelpPage() {
  const [tab, setTab] = useState<Tab>("about");

  return (
    <div className="space-y-6" data-testid="help-page">
      <div
        className="flex items-center justify-between"
        data-testid="help-header"
      >
        <div>
          <h1 className="text-2xl font-bold">Help & Reference</h1>
          <p className="text-muted-foreground text-sm mt-1">
            norirobotics-mcp — MCP control surface for the Nori A3
          </p>
        </div>
        <span className="text-sm text-amber-400 font-semibold border border-amber-500/30 px-3 py-1 rounded-full bg-amber-500/10">
          Ships Fall 2026
        </span>
      </div>

      <div
        className="flex gap-1 bg-muted/30 p-1 rounded-xl border border-border w-fit"
        data-testid="help-tabs"
      >
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            data-testid={`help-tab-${t.id}`}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              tab === t.id
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "about" && (
        <div className="space-y-6">
          <Card className="border-amber-500/30 bg-amber-500/5">
            <CardTitle className="text-base mb-2 text-amber-400">
              No hardware yet
            </CardTitle>
            <p className="text-sm text-muted-foreground">
              Nori A3 is a $1,688, 19-DOF wheeled bimanual home robot from Nori
              Robotics (YC S26, San Francisco), founded by Antonio Li while
              researching robot teaching-by-demonstration at Columbia. It ships
              Fall 2026 — this repo wraps the robot's real SDK (nori-sdk, WebRTC
              + Supabase) and defaults every session to that SDK's own mock
              robot.
            </p>
          </Card>

          <Card>
            <CardTitle className="text-base mb-3">Hardware</CardTitle>
            <table className="w-full border-collapse text-sm">
              <tbody>
                {[
                  [
                    "DOF",
                    "19 (2x 7+1-DOF arms + 1 lift axis + differential drive base)",
                  ],
                  ["Arm reach / payload", "55cm reach, 1.5kg payload per arm"],
                  [
                    "Lift",
                    "3-stage telescoping column, 69-145cm, 76cm travel @ 30mm/s",
                  ],
                  [
                    "Actuators",
                    "Feetech STS-series bus servos (STS3095/3250/3215), torque-graded",
                  ],
                  [
                    "Gripper",
                    "Soft TPU fingers, sensorless force sensing from servo current",
                  ],
                  [
                    "Compute",
                    "Raspberry Pi 5, 4GB — bus I/O + control loop only, no onboard inference",
                  ],
                  ["Cameras", "4x 720p @ 30fps (grippers x2, head, neck)"],
                  ["LiDAR", "2D, 12m range, 8-12Hz scan"],
                  ["Battery", "432Wh, 6-8h"],
                ].map(([k, v]) => (
                  <tr key={k} className="border-b border-border last:border-0">
                    <td className="py-1.5 pr-4 font-medium text-foreground w-1/3">
                      {k}
                    </td>
                    <td className="py-1.5 text-muted-foreground">{v}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>

          <Card>
            <CardTitle className="text-base mb-3">Lineage</CardTitle>
            <p className="text-sm text-muted-foreground">
              The team's prior version ran on the open-source XLeRobot base
              (SO-100/SO-101 arms + Lekiwi base + IKEA cart, built on Hugging
              Face's LeRobot ecosystem). The A3 paper states it "shares none of
              that hardware" — a clean-sheet redesign — but the lift,
              actuator-protection stack, and sensorless force channel carried
              forward. Recordings are written in LeRobot-compatible format, so
              existing Hugging Face training pipelines apply without conversion.
            </p>
          </Card>

          <Card>
            <CardTitle className="text-base mb-3">
              Community (Hacker News launch)
            </CardTitle>
            <p className="text-sm text-muted-foreground">
              97 points, 36 comments. Praise: price, wheeled-not-bipedal safety,
              open SDK. Criticism: RC-servo precision vs. QDD actuators
              (CubeMars/MyActuator named), staged-demo skepticism,
              cloud-mediated WebRTC control privacy concerns, and category-level
              skepticism about home robotics generally. See{" "}
              <code className="text-primary">
                nori_info(operation="community")
              </code>{" "}
              for the full, sourced breakdown.
            </p>
          </Card>

          <Card>
            <CardTitle className="text-base mb-1">
              Part of the sandraschi Robotics + VR Fleet
            </CardTitle>
            <p className="text-sm text-muted-foreground mb-3">
              norirobotics-mcp isn't a standalone wrapper — it registers with{" "}
              <code className="text-primary">robotics-mcp</code> as a member
              robot and plugs into a set of VR-platform MCP servers for
              virtual-first testing before hardware ships.
            </p>
            <p className="text-sm font-semibold text-foreground mb-1">
              Robotics fleet peers
            </p>
            <div className="text-sm space-y-1.5 mb-4">
              {fleetPeers.map((p) => (
                <div key={p.id}>
                  <code className="text-primary text-sm">{p.id}</code>
                  <span className="text-sm text-muted-foreground">
                    {" "}
                    — {p.note}
                  </span>
                </div>
              ))}
            </div>
            <p className="text-sm font-semibold text-foreground mb-1">
              VR crossconnects — using other fleet repos (virtual twins via
              robotics-mcp + VR bridges — not standalone in this repo)
            </p>
            <div className="text-sm space-y-1.5">
              {vrCrossconnects.map((p) => (
                <div key={p.id}>
                  <code className="text-primary text-sm">{p.id}</code>
                  <span className="text-sm text-muted-foreground">
                    {" "}
                    — {p.note}
                  </span>
                </div>
              ))}
            </div>
          </Card>

          <Card className="border-red-500/30 bg-red-500/5">
            <CardTitle className="text-base mb-2 text-red-400">
              Safety
            </CardTitle>
            <p className="text-sm text-muted-foreground">
              Every nori_control call maps 1:1 onto a real nori_sdk method —
              this server does not reinterpret targets. Calibration clamping,
              stall detection, and thermal cutoff live in the robot's own
              protection stack, not in this repo. Treat any real (non-mock)
              connection as safety-critical.
            </p>
          </Card>
        </div>
      )}

      {tab === "quickstart" && (
        <div className="space-y-6">
          <Card>
            <CardTitle className="text-base mb-2">Quick start</CardTitle>
            <ol className="text-sm text-muted-foreground list-decimal pl-5 space-y-2">
              <li>
                Backend: <code className="text-primary">uv sync</code> then{" "}
                <code className="text-primary">
                  uv run python -m norirobotics_mcp --serve
                </code>{" "}
                (backend, see <code>/api/capabilities</code>)
              </li>
              <li>
                Dashboard:{" "}
                <code className="text-primary">
                  cd web_sota; npm install; npm run dev
                </code>{" "}
                (frontend, see <code>/api/capabilities</code>) or double-click{" "}
                <code>start.bat</code>
              </li>
              <li>
                MCP client (stdio):{" "}
                <code className="text-primary">uv run norirobotics-mcp</code>
              </li>
              <li>
                Real robot: set{" "}
                <code className="text-primary">NORI_MCP_SUPABASE_*</code> +{" "}
                <code className="text-primary">NORI_MCP_ROBOT_ROOM</code> — see
                Settings
              </li>
            </ol>
          </Card>
        </div>
      )}

      {tab === "reference" && (
        <div className="space-y-6">
          <Card>
            <CardTitle className="text-base mb-2">MCP tools</CardTitle>
            <div className="text-sm space-y-1">
              <div className="grid grid-cols-[1fr_2fr_2fr] gap-2 font-semibold text-foreground border-b border-border pb-1 mb-1">
                <span>Tool</span>
                <span>Operations</span>
                <span>Description</span>
              </div>
              {toolsList.map((t) => (
                <div
                  key={t.name}
                  className="grid grid-cols-[1fr_2fr_2fr] gap-2 text-muted-foreground"
                >
                  <code className="text-primary text-sm">{t.name}</code>
                  <code className="text-sm">{t.op}</code>
                  <span className="text-sm">{t.desc}</span>
                </div>
              ))}
            </div>
          </Card>
          <Card>
            <CardTitle className="text-base mb-2">REST API endpoints</CardTitle>
            <div className="text-sm space-y-1">
              {[
                ["GET /api/health", "Server health"],
                ["GET /api/hero", "Spec sheet + fleet peers"],
                ["GET /api/tools", "Registered MCP tools manifest"],
                ["GET /api/session", "Session status"],
                ["POST /api/session/connect", "Open a session (real or mock)"],
                ["POST /api/control/estop", "Emergency stop"],
                ["POST /api/recording/start", "Start an episode recording"],
              ].map(([path, desc]) => (
                <div
                  key={path}
                  className="grid grid-cols-[2fr_3fr] gap-2 text-muted-foreground"
                >
                  <code className="text-sm text-primary">{path}</code>
                  <span className="text-sm">{desc}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {tab === "faq" && (
        <Card>
          <CardTitle className="text-base mb-3">FAQ</CardTitle>
          <div className="space-y-4">
            {faq.map((item) => (
              <div key={item.q}>
                <p className="text-sm font-semibold text-foreground">
                  {item.q}
                </p>
                <p className="text-sm text-muted-foreground mt-1">{item.a}</p>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
