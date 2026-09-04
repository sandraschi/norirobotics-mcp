import { useState } from "react";
import { apiPost } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";

export function RecordingPage() {
  const [task, setTask] = useState("");
  const [result, setResult] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  const start = async () => {
    setBusy(true);
    try {
      setResult(await apiPost("/api/recording/episode_start", { task }));
    } finally {
      setBusy(false);
    }
  };

  const stop = async () => {
    setBusy(true);
    try {
      setResult(await apiPost("/api/recording/episode_stop"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="recording-page">
      <h1 className="text-2xl font-bold">Recording</h1>
      <p className="text-sm text-muted-foreground" data-testid="recording-desc">
        Requires an open session. <code>episode_start</code>/
        <code>episode_stop</code> map directly onto nori_sdk's own recording
        verbs and persist server-side (Nori's backend) in LeRobot-compatible
        format — the handoff point into <code>vla-mcp</code> / Hugging Face
        LeRobot training pipelines.
      </p>
      <Card className="space-y-3" data-testid="recording-card">
        <CardTitle>Episode</CardTitle>
        <input
          data-testid="recording-task"
          className="w-full rounded-md border border-border bg-secondary px-3 py-2 text-sm"
          placeholder="task description (e.g. pour water into cup)"
          value={task}
          onChange={(e) => setTask(e.target.value)}
        />
        <div className="flex gap-2">
          <Button onClick={start} disabled={busy} data-testid="recording-start">
            Start episode
          </Button>
          <Button
            variant="outline"
            onClick={stop}
            disabled={busy}
            data-testid="recording-stop"
          >
            Stop episode
          </Button>
        </div>
      </Card>
      {result != null && (
        <Card>
          <CardTitle className="mb-2">Last result</CardTitle>
          <pre className="text-xs overflow-x-auto whitespace-pre-wrap text-muted-foreground">
            {JSON.stringify(result, null, 2)}
          </pre>
        </Card>
      )}
    </div>
  );
}
