import { useEffect, useState } from "react";
import { apiGet } from "@/api/client";
import { Card, CardTitle } from "@/components/ui/card";

type Tool = {
  name: string;
  description: string;
  params?: Record<string, string>;
};

export function ToolsPage() {
  const [tools, setTools] = useState<Tool[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<{ tools: Tool[] }>("/api/tools")
      .then((d) => setTools(d.tools ?? []))
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  return (
    <div className="space-y-4" data-testid="tools-page">
      <h1 className="text-2xl font-bold">Tools</h1>
      <p className="text-sm text-muted-foreground" data-testid="tools-desc">
        MCP tools exposed by this server — discovered live from{" "}
        <code>/api/tools</code>, not hardcoded.
      </p>

      {error && (
        <Card
          className="p-4 border-amber-500/30 bg-amber-500/10"
          data-testid="tools-error"
        >
          <p className="text-sm text-amber-300">
            Failed to load tools: {error}
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

      {tools === null && !error && (
        <Card className="p-8 text-center" data-testid="tools-loading">
          <p className="text-sm text-muted-foreground">Loading tools…</p>
        </Card>
      )}

      {tools !== null && tools.length === 0 && !error && (
        <Card className="p-8 text-center" data-testid="tools-empty">
          <p className="text-sm text-muted-foreground">No tools registered.</p>
          <p className="text-sm text-muted-foreground mt-1">
            Check backend on /api/tools
          </p>
        </Card>
      )}

      {tools !== null && tools.length > 0 && (
        <div className="grid gap-3" data-testid="tools-list">
          {tools.map((t) => (
            <Card key={t.name} className="p-4">
              <CardTitle className="text-sm">{t.name}</CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                {t.description}
              </p>
              {t.params && Object.keys(t.params).length > 0 && (
                <pre className="text-sm mt-2 p-2 rounded bg-muted/40 overflow-x-auto whitespace-pre-wrap">
                  {JSON.stringify(t.params, null, 2)}
                </pre>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
