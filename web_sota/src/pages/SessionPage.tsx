import { useCallback, useEffect, useState } from "react";
import { apiGet, apiPost } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";

type SessionStatus = {
  success: boolean;
  connected: boolean;
  mock?: boolean;
  message?: string;
  status?: unknown;
  telemetry?: unknown;
  camera_layout?: unknown;
};

export function SessionPage() {
  const [status, setStatus] = useState<SessionStatus | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(() => {
    apiGet<SessionStatus>("/api/session")
      .then(setStatus)
      .catch(() => setStatus(null));
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const connect = async () => {
    setBusy(true);
    try {
      await apiPost("/api/session/connect");
      refresh();
    } finally {
      setBusy(false);
    }
  };

  const disconnect = async () => {
    setBusy(true);
    try {
      await apiPost("/api/session/disconnect");
      refresh();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Session</h1>
      <Card>
        <div className="flex items-center justify-between mb-3">
          <CardTitle>Connection</CardTitle>
          <span
            className={`text-xs px-2 py-0.5 rounded-full ${
              status?.connected
                ? "bg-green-500/10 text-green-400 border border-green-500/30"
                : "bg-muted text-muted-foreground border border-border"
            }`}
          >
            {status?.connected
              ? status.mock
                ? "connected (mock)"
                : "connected (real)"
              : "disconnected"}
          </span>
        </div>
        <div className="flex gap-2">
          <Button onClick={connect} disabled={busy || status?.connected}>
            Connect
          </Button>
          <Button
            variant="outline"
            onClick={disconnect}
            disabled={busy || !status?.connected}
          >
            Disconnect
          </Button>
          <Button variant="ghost" onClick={refresh} disabled={busy}>
            Refresh
          </Button>
        </div>
      </Card>
      {status?.connected && (
        <Card>
          <CardTitle className="mb-2">Telemetry</CardTitle>
          <pre className="text-xs overflow-x-auto whitespace-pre-wrap text-muted-foreground">
            {JSON.stringify(
              {
                status: status.status,
                telemetry: status.telemetry,
                camera_layout: status.camera_layout,
              },
              null,
              2,
            )}
          </pre>
        </Card>
      )}
      {!status?.connected && (
        <p className="text-sm text-muted-foreground">
          Not connected. Nori A3 ships Fall 2026 — clicking Connect here opens{" "}
          <code>nori_sdk.mock.mock_session()</code> unless real Supabase
          credentials are configured (see docs/ONBOARDING.md).
        </p>
      )}
    </div>
  );
}
