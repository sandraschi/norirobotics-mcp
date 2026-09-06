import { useState } from "react";
import { apiPost } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";

type SpawnResult = {
  success?: boolean;
  message?: string;
  error?: string;
  platform?: string;
  mesh_path?: string;
  spawned?: boolean;
  mock?: boolean;
  bridge_reachable?: boolean;
  details?: Record<string, unknown>;
};

type Platform = {
  id: string;
  title: string;
  desc: string;
  mesh: string;
  spawnOp: string | null;
  statusOp: string | null;
};

const PLATFORMS: Platform[] = [
  {
    id: "unity",
    title: "Unity3D",
    desc: "nori_a3_posed.glb via unity3d-mcp model depot + spawn_fixture. Real mesh, not a box primitive.",
    mesh: "/api/model/nori_a3.glb",
    spawnOp: "unity_spawn",
    statusOp: "unity_status",
  },
  {
    id: "overte",
    title: "Overte",
    desc: "Same GLB via overte-mcp. Verified live — fixture-spawner/animate/depot pattern.",
    mesh: "/api/model/nori_a3.glb",
    spawnOp: "overte_spawn",
    statusOp: null,
  },
  {
    id: "godot",
    title: "Godot 4",
    desc: "Same GLB via godot-mcp TCP bridge + model/texture asset depot.",
    mesh: "/api/model/nori_a3.glb",
    spawnOp: "godot_spawn",
    statusOp: null,
  },
  {
    id: "mujoco",
    title: "MuJoCo",
    desc: "Local physics viewer from this repo's models/nori_description/ URDF — no fleet repo needed.",
    mesh: "/api/model/nori_a3.glb",
    spawnOp: "mujoco_view",
    statusOp: null,
  },
  {
    id: "isaac",
    title: "Isaac Sim",
    desc: "NVIDIA Omniverse USD import of the GLB/URDF for a sim2real physics twin via isaac-mcp.",
    mesh: "/api/model/nori_a3.glb",
    spawnOp: "isaac_export",
    statusOp: null,
  },
];

export function VRPage() {
  const [results, setResults] = useState<Record<string, SpawnResult>>({});
  const [busy, setBusy] = useState<Record<string, boolean>>({});

  const call = async (platformId: string, op: string) => {
    const key = `${platformId}:${op}`;
    setBusy((b) => ({ ...b, [key]: true }));
    try {
      const data = await apiPost<SpawnResult>("/api/vr", { operation: op });
      setResults((r) => ({ ...r, [platformId]: data }));
    } catch (e) {
      setResults((r) => ({
        ...r,
        [platformId]: {
          success: false,
          error: e instanceof Error ? e.message : String(e),
        },
      }));
    } finally {
      setBusy((b) => ({ ...b, [key]: false }));
    }
  };

  return (
    <div className="space-y-4" data-testid="vr-page">
      <h1 className="text-2xl font-bold">VR Spawn</h1>
      <p className="text-sm text-muted-foreground" data-testid="vr-desc">
        Push the Nori A3 virtual twin into VR/physics environs. This repo
        supplies the mesh — other fleet repos (robotics-mcp + VR bridges) do the
        spawning. Results land in the activity log too.
      </p>

      <div className="grid gap-3 md:grid-cols-2" data-testid="vr-platforms">
        {PLATFORMS.map((p) => {
          const res = results[p.id];
          return (
            <Card
              key={p.id}
              className="p-4 space-y-3"
              data-testid={`vr-card-${p.id}`}
            >
              <CardTitle className="text-base">{p.title}</CardTitle>
              <p className="text-sm text-muted-foreground">{p.desc}</p>
              <div className="flex gap-2 flex-wrap">
                {p.statusOp && (
                  <Button
                    variant="outline"
                    size="sm"
                    data-testid={`vr-status-${p.id}`}
                    disabled={!!busy[`${p.id}:${p.statusOp}`]}
                    onClick={() => p.statusOp && call(p.id, p.statusOp)}
                  >
                    {busy[`${p.id}:${p.statusOp}`] ? "Probing…" : "Status"}
                  </Button>
                )}
                {p.spawnOp && (
                  <Button
                    size="sm"
                    data-testid={`vr-spawn-${p.id}`}
                    disabled={!!busy[`${p.id}:${p.spawnOp}`]}
                    onClick={() => p.spawnOp && call(p.id, p.spawnOp)}
                  >
                    {busy[`${p.id}:${p.spawnOp}`]
                      ? "Spawning…"
                      : p.id === "mujoco"
                        ? "View"
                        : p.id === "isaac"
                          ? "Export"
                          : "Spawn"}
                  </Button>
                )}
                <a
                  className="text-sm text-primary underline self-center"
                  data-testid={`vr-mesh-${p.id}`}
                  href={p.mesh}
                  download
                >
                  Download GLB
                </a>
              </div>
              {res && (
                <div
                  data-testid={`vr-result-${p.id}`}
                  className={`rounded-lg px-3 py-2 text-sm border ${
                    res.success
                      ? "bg-green-500/10 border-green-500/30"
                      : "bg-red-500/10 border-red-500/30"
                  }`}
                >
                  <div className="flex gap-2 items-center flex-wrap">
                    <span
                      className={`text-sm font-semibold ${
                        res.success ? "text-green-400" : "text-red-400"
                      }`}
                    >
                      {res.success ? "OK" : "FAILED"}
                    </span>
                    {res.spawned !== undefined && (
                      <span className="text-sm text-muted-foreground">
                        {res.spawned
                          ? "live via fleet bridge"
                          : "mock — bridge not running"}
                      </span>
                    )}
                  </div>
                  <p className="mt-1 whitespace-pre-wrap break-words">
                    {res.message ?? res.error ?? "No response"}
                  </p>
                  {res.mesh_path && (
                    <p className="text-sm text-muted-foreground mt-1 font-mono break-all">
                      {res.mesh_path}
                    </p>
                  )}
                </div>
              )}
            </Card>
          );
        })}

        <Card className="p-4 space-y-3" data-testid="vr-card-resonite">
          <CardTitle className="text-base">Resonite</CardTitle>
          <p className="text-sm text-muted-foreground">
            Via robotics-mcp robot_virtual/vbot_crud
            (robot_type=&quot;nori_a3&quot;) through resonite-mcp
            ResoniteLink.spawn_mesh — decimated mesh-JSON, verified. Not part of
            this repo&apos;s nori_vr yet; use the robotics-mcp hub directly.
          </p>
          <a
            className="text-sm text-primary underline"
            data-testid="vr-mesh-resonite"
            href="/api/model/nori_a3.glb"
            download
          >
            Download GLB
          </a>
        </Card>
      </div>
    </div>
  );
}
