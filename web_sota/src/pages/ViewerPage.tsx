import { Box, PersonStanding, RotateCcw } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";
import { BotViewer } from "@/lib/bot-viewer";

const MODEL_URL = "/api/model/nori_a3_rig.glb";

export function ViewerPage() {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<BotViewer | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "error">(
    "loading",
  );
  const [error, setError] = useState("");
  const [stats, setStats] = useState<{
    vertexCount: number;
    triangleCount: number;
    jointsFound: number;
  } | null>(null);
  const [wireframe, setWireframe] = useState(false);
  const [waving, setWaving] = useState(false);

  useEffect(() => {
    if (!containerRef.current) return;
    const viewer = new BotViewer(containerRef.current);
    viewerRef.current = viewer;
    viewer.startLoop();

    setStatus("loading");
    viewer
      .loadModel(MODEL_URL)
      .then((s) => {
        setStats(s);
        setStatus("ready");
      })
      .catch((e) => {
        setError(e instanceof Error ? e.message : String(e));
        setStatus("error");
      });

    return () => {
      viewer.destroy();
      viewerRef.current = null;
    };
  }, []);

  const toggleWireframe = () => {
    const next = !wireframe;
    setWireframe(next);
    viewerRef.current?.setWireframe(next);
  };

  const toggleWave = () => {
    const next = !waving;
    setWaving(next);
    viewerRef.current?.setDemoAnimation(next);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Box className="h-6 w-6 text-primary" />
            3D Viewer
          </h1>
          <p className="text-sm text-muted-foreground">
            Real Nori A3 mesh, expanded from the vendored URDF and posed via
            MuJoCo forward kinematics.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`text-xs px-2 py-0.5 rounded-full border ${
              status === "ready"
                ? "bg-green-500/10 text-green-400 border-green-500/30"
                : status === "error"
                  ? "bg-red-500/10 text-red-400 border-red-500/30"
                  : "bg-muted text-muted-foreground border-border"
            }`}
          >
            {status === "loading" && "Loading model…"}
            {status === "ready" &&
              `${stats?.triangleCount.toLocaleString()} tris`}
            {status === "error" && "Failed to load"}
          </span>
          <Button
            variant={waving ? "default" : "outline"}
            size="sm"
            onClick={toggleWave}
            disabled={status !== "ready" || !stats?.jointsFound}
          >
            <PersonStanding className="h-4 w-4 mr-1" />
            {waving ? "Stop wave" : "Wave demo"}
          </Button>
          <Button variant="outline" size="sm" onClick={toggleWireframe}>
            {wireframe ? "Solid" : "Wireframe"}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => viewerRef.current?.resetView()}
          >
            <RotateCcw className="h-4 w-4 mr-1" />
            Reset view
          </Button>
        </div>
      </div>

      <Card className="p-0 overflow-hidden">
        <div ref={containerRef} className="h-[65vh] w-full relative">
          {status === "error" && (
            <div className="absolute inset-0 flex items-center justify-center bg-background/80">
              <div className="text-center max-w-md px-4">
                <p className="text-sm text-red-400 mb-2">
                  Could not load the model.
                </p>
                <p className="text-xs text-muted-foreground">{error}</p>
                <p className="text-xs text-muted-foreground mt-2">
                  Run <code>scripts/export_posed_mesh.py</code> in the repo to
                  (re)generate{" "}
                  <code>models/nori_description/nori_a3_rig.glb</code>.
                </p>
              </div>
            </div>
          )}
        </div>
      </Card>

      <Card>
        <CardTitle className="mb-2">Controls</CardTitle>
        <ul className="text-sm text-muted-foreground space-y-1">
          <li>Left-drag — orbit</li>
          <li>Right-drag — pan</li>
          <li>Scroll / pinch — zoom</li>
          <li>
            Wave demo — procedurally rotates the left arm's shoulder, elbow, and
            wrist joints (real axes/limits from the URDF), not a physically
            simulated trajectory
          </li>
        </ul>
      </Card>
    </div>
  );
}
