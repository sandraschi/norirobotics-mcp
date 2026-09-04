import { useState } from "react";
import { apiPost } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";

export function ControlPage() {
  const [result, setResult] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  const estop = async () => {
    setBusy(true);
    try {
      setResult(await apiPost("/api/control/estop"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="control-page">
      <h1 className="text-2xl font-bold">Control</h1>
      <p className="text-sm text-muted-foreground" data-testid="control-desc">
        Requires an open session (see the Session page). Full motion surface —
        jog, action, Cartesian pose — is exposed via the{" "}
        <code>nori_control</code> MCP tool; this page ships the one control
        every operator needs at a glance: e-stop.
      </p>
      <Card data-testid="control-estop-card">
        <CardTitle className="mb-3">Emergency stop</CardTitle>
        <Button
          variant="destructive"
          onClick={estop}
          disabled={busy}
          data-testid="control-estop"
        >
          E-STOP
        </Button>
      </Card>
      {result != null && (
        <Card data-testid="control-result">
          <CardTitle className="mb-2">Last result</CardTitle>
          <pre className="text-xs overflow-x-auto whitespace-pre-wrap text-muted-foreground">
            {JSON.stringify(result, null, 2)}
          </pre>
        </Card>
      )}
    </div>
  );
}
