import { useEffect, useState } from "react";
import { apiGet } from "@/api/client";
import { Card, CardTitle } from "@/components/ui/card";

type LogEntry = {
  id: string;
  timestamp: string;
  level: string;
  detail: string;
};

export function InboxPage() {
  const [entries, setEntries] = useState<LogEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<{ entries: LogEntry[] }>("/api/logs?limit=20")
      .then((d) => setEntries(d.entries ?? []))
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  return (
    <div className="space-y-4" data-testid="inbox-page">
      <h1 className="text-2xl font-bold">Inbox</h1>
      <p className="text-sm text-muted-foreground" data-testid="inbox-desc">
        Recent activity from the server log — newest first. This is the
        fleet-standard Inbox surface.
      </p>

      {error && (
        <Card
          className="p-4 border-amber-500/30 bg-amber-500/10"
          data-testid="inbox-error"
        >
          <p className="text-sm text-amber-300">
            Failed to load inbox: {error}
          </p>
          <button
            type="button"
            className="text-sm text-primary underline mt-2"
            onClick={() => window.location.reload()}
          >
            Retry
          </button>
        </Card>
      )}

      {entries === null && !error && (
        <Card className="p-8 text-center" data-testid="inbox-loading">
          <p className="text-sm text-muted-foreground">Loading inbox…</p>
        </Card>
      )}

      {entries !== null && entries.length === 0 && !error && (
        <Card className="p-8 text-center" data-testid="inbox-empty">
          <p className="text-sm text-muted-foreground">Inbox is empty.</p>
          <p className="text-sm text-muted-foreground mt-1">
            Perform a session or control action to generate activity.
          </p>
        </Card>
      )}

      {entries !== null && entries.length > 0 && (
        <div className="space-y-2" data-testid="inbox-list">
          {entries.map((e) => (
            <Card key={e.id} className="p-3">
              <div className="flex items-center gap-2">
                <span className="text-sm font-mono text-muted-foreground">
                  {e.timestamp.split("T")[1] ?? e.timestamp}
                </span>
                <span className="text-sm px-2 py-0.5 rounded-full bg-muted border border-border">
                  {e.level}
                </span>
              </div>
              <CardTitle className="text-sm mt-1">{e.detail}</CardTitle>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
