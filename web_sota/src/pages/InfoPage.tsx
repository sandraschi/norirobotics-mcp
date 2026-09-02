import { useEffect, useState } from "react";
import { apiGet } from "@/api/client";
import { Card, CardTitle } from "@/components/ui/card";

type FleetPeer = { id: string; note: string };
type HeroResponse = { hero: Record<string, unknown>; fleet_peers: FleetPeer[] };

export function InfoPage() {
  const [data, setData] = useState<HeroResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    apiGet<HeroResponse>("/api/hero")
      .then(setData)
      .catch((e) => setErr(e instanceof Error ? e.message : String(e)));
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Info</h1>
      <p className="text-sm text-muted-foreground">
        Specs, SDK links, predecessor lineage, and community reaction. Full
        detail lives behind the <code>nori_info(operation=...)</code> MCP tool —
        this page is a quick spec + fleet-map view; ask Claude for{" "}
        <code>community</code> or <code>actuator_upgrade</code> for the full
        Hacker News writeup.
      </p>
      {err && <div className="text-sm text-red-400">{err}</div>}
      {data && (
        <>
          <Card>
            <CardTitle className="mb-2">Spec sheet</CardTitle>
            <pre className="text-xs overflow-x-auto whitespace-pre-wrap text-muted-foreground">
              {JSON.stringify(data.hero, null, 2)}
            </pre>
          </Card>
          <Card>
            <CardTitle className="mb-2">Fleet peers</CardTitle>
            <ul className="space-y-2 text-sm">
              {data.fleet_peers.map((p) => (
                <li key={p.id}>
                  <span className="text-primary font-mono">{p.id}</span> —{" "}
                  {p.note}
                </li>
              ))}
            </ul>
          </Card>
        </>
      )}
    </div>
  );
}
