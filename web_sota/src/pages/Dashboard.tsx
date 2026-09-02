import {
  Bot,
  Cpu,
  Gauge,
  Ruler,
  Terminal,
  Video,
  Weight,
  Zap,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet } from "@/api/client";
import { Card, CardTitle } from "@/components/ui/card";

type Health = { status: string; service: string };
type HeroSpecs = {
  dof: number;
  arms: string;
  lift: string;
  weight_kg: number;
  actuators: string;
  compute: string;
  battery: string;
};
type HeroData = {
  product: string;
  vendor: string;
  tagline: string;
  price_usd: number;
  ships: string;
  specs: HeroSpecs;
};
type FullResponse = { hero: HeroData };

export function Dashboard() {
  const [health, setHealth] = useState<Health | null>(null);
  const [hero, setHero] = useState<HeroData | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const [h, f] = await Promise.all([
        apiGet<Health>("/api/health"),
        apiGet<FullResponse>("/api/hero"),
      ]);
      setHealth(h);
      setHero(f?.hero ?? null);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const s = hero?.specs;
  const statCards = [
    { label: "DOF", value: s ? String(s.dof) : "—", icon: Gauge },
    { label: "Weight", value: s ? `${s.weight_kg}kg` : "—", icon: Weight },
    {
      label: "Lift travel",
      value: s ? (s.lift.split(",")[1]?.trim() ?? s.lift) : "—",
      icon: Ruler,
    },
    { label: "Battery", value: s ? s.battery : "—", icon: Zap },
    { label: "Compute", value: s ? "Pi 5, 4GB" : "—", icon: Cpu },
    { label: "Price", value: hero ? `$${hero.price_usd}` : "—", icon: Bot },
  ];

  const tiles = [
    {
      to: "/session",
      label: "Session",
      desc: "Connect (real or mock), inspect telemetry",
      icon: Gauge,
    },
    {
      to: "/control",
      label: "Control",
      desc: "Motion, pose, e-stop, fault reset",
      icon: Terminal,
    },
    {
      to: "/recording",
      label: "Recording",
      desc: "LeRobot-format episode capture",
      icon: Video,
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Nori A3</h1>
          <p className="text-muted-foreground text-base mt-1 max-w-2xl">
            {hero?.tagline ?? "Affordable bimanual mobile manipulator"}
          </p>
          <p className="text-amber-400 text-sm font-semibold mt-2 flex items-center gap-2">
            <Zap size={16} />
            Ships {hero?.ships ?? "Fall 2026"} — no physical unit here yet.
            Session tools default to nori_sdk's own mock robot.
          </p>
        </div>
        <div className="text-right text-xs text-muted-foreground">
          <div>{hero?.vendor ?? "—"}</div>
          <div className="mt-1">
            <span
              className={`inline-block w-2 h-2 rounded-full mr-1 ${
                health?.status === "ok" ? "bg-green-500" : "bg-amber-500"
              }`}
            />
            {health?.status ?? "offline"}
          </div>
        </div>
      </div>

      {err && (
        <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm">
          API: {err} — start backend on port 11970:{" "}
          <code className="text-xs">
            uv run python -m norirobotics_mcp --serve
          </code>
        </div>
      )}

      <div>
        <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <Cpu size={20} className="text-primary" /> Specifications
        </h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {statCards.map((st) => (
            <Card key={st.label}>
              <div className="flex items-center gap-3">
                <st.icon className="h-5 w-5 text-primary shrink-0" />
                <div className="min-w-0">
                  <CardTitle className="text-xs text-muted-foreground font-normal uppercase tracking-wider">
                    {st.label}
                  </CardTitle>
                  <p className="text-xl font-semibold mt-0.5">{st.value}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {tiles.map((t) => (
          <Link key={t.to} to={t.to} className="block group">
            <Card className="h-full transition-transform group-hover:scale-[1.01]">
              <div className="flex gap-3">
                <t.icon className="h-8 w-8 text-primary shrink-0" />
                <div>
                  <CardTitle>{t.label}</CardTitle>
                  <p className="text-sm text-muted-foreground mt-1">{t.desc}</p>
                </div>
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
