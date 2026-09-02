import { useCallback, useEffect, useState } from "react";

type LogEntry = {
  id: string;
  timestamp: string;
  level: string;
  detail: string;
};

const LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR"];
const LEVEL_COLORS: Record<string, string> = {
  ERROR: "text-red-400 bg-red-950/40",
  WARNING: "text-yellow-400 bg-yellow-950/40",
  INFO: "text-blue-300 bg-blue-950/30",
  DEBUG: "text-slate-500 bg-slate-900/30",
};

export default function Logging() {
  const [entries, setEntries] = useState<LogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [level, setLevel] = useState("");
  const [search, setSearch] = useState("");

  const fetchLogs = useCallback(async () => {
    const params = new URLSearchParams({ limit: "100" });
    if (level) params.set("level", level);
    if (search) params.set("search", search);
    try {
      const r = await fetch(`/api/logs?${params}`);
      const d = await r.json();
      setEntries(d.entries ?? []);
      setTotal(d.total ?? 0);
    } catch {
      /* backend offline */
    }
  }, [level, search]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-bold mr-2">Logs</h1>
        <select
          className="h-8 rounded border border-border bg-secondary px-2 text-xs"
          value={level}
          onChange={(e) => setLevel(e.target.value)}
        >
          <option value="">All levels</option>
          {LEVELS.map((l) => (
            <option key={l} value={l}>
              {l}
            </option>
          ))}
        </select>
        <input
          className="h-8 w-48 rounded border border-border bg-secondary px-2 text-xs"
          placeholder="Search..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <span className="text-xs text-muted-foreground ml-auto">
          {total} entries
        </span>
      </div>

      <div className="h-[60vh] overflow-auto rounded-lg border border-border bg-background/40 p-3 font-mono text-xs leading-relaxed">
        {entries.length === 0 && (
          <div className="text-muted-foreground text-center py-12">
            No log entries yet
          </div>
        )}
        {entries.map((e) => (
          <div
            key={e.id}
            className="flex gap-3 py-0.5 hover:bg-muted/30 rounded px-1"
          >
            <span className="text-muted-foreground w-20 shrink-0">
              {e.timestamp.split("T")[1] ?? e.timestamp}
            </span>
            <span
              className={`w-16 shrink-0 text-center rounded text-[10px] font-bold ${LEVEL_COLORS[e.level] ?? ""}`}
            >
              {e.level}
            </span>
            <span className="break-all">{e.detail}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
