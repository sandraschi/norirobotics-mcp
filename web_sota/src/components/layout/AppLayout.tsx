import {
  Bot,
  Box,
  Gauge,
  HelpCircle,
  Home,
  Inbox,
  Menu,
  MessageSquare,
  ScrollText,
  Settings,
  Sparkles,
  Terminal,
  Video,
  Wrench,
  X,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useZoom } from "@/lib/use-zoom";
import { cn } from "@/lib/utils";

async function checkBackendHealth(): Promise<{ ok: boolean; error?: string }> {
  try {
    const r = await fetch("/api/health");
    if (!r.ok) return { ok: false, error: `HTTP ${r.status}` };
    return { ok: true };
  } catch (e) {
    return {
      ok: false,
      error: e instanceof Error ? e.message : "Network error",
    };
  }
}

type ActiveRobotProfile = {
  id: string;
  name: string;
  kind: "physical" | "virtual";
} | null;

async function fetchActiveRobotProfile(): Promise<ActiveRobotProfile> {
  try {
    const r = await fetch("/api/robot-profiles/active");
    if (!r.ok) return null;
    const d = await r.json();
    return d.active ?? null;
  } catch {
    return null;
  }
}

const nav = [
  { to: "/dashboard", label: "Dashboard", icon: Home },
  { to: "/inbox", label: "Inbox", icon: Inbox },
  { to: "/tools", label: "Tools", icon: Wrench },
  { to: "/skills", label: "Skills", icon: Sparkles },
  { to: "/chat", label: "Chat", icon: MessageSquare },
  { to: "/info", label: "Info", icon: Bot },
  { to: "/session", label: "Session", icon: Gauge },
  { to: "/control", label: "Control", icon: Terminal },
  { to: "/viewer", label: "3D Viewer", icon: Box },
  { to: "/recording", label: "Recording", icon: Video },
  { to: "/settings", label: "Settings", icon: Settings },
  { to: "/help", label: "Help", icon: HelpCircle },
  { to: "/logging", label: "Logging", icon: ScrollText },
] as const;

export function AppLayout() {
  const [open, setOpen] = useState(true);
  const [mobile, setMobile] = useState(false);
  const [backendOk, setBackendOk] = useState<boolean | null>(null);
  const [activeRobot, setActiveRobot] = useState<ActiveRobotProfile>(null);
  const loc = useLocation();

  useZoom();

  const refreshBackend = useCallback(async () => {
    const h = await checkBackendHealth();
    setBackendOk(h.ok);
    setActiveRobot(await fetchActiveRobotProfile());
  }, []);

  // Poll via HTTP every 10s (works in dev browser) - one extra fetch piggybacked
  // on the existing backend-health poll rather than a second interval.
  useEffect(() => {
    refreshBackend();
    const interval = setInterval(refreshBackend, 10_000);
    return () => clearInterval(interval);
  }, [refreshBackend]);

  // Listen for Tauri "backend-status" event (instant updates in NSIS WebView)
  useEffect(() => {
    let unlisten: (() => void) | undefined;
    (async () => {
      try {
        const { listen } = await import("@tauri-apps/api/event");
        unlisten = await listen<string>("backend-status", (event) => {
          if (event.payload === "ready") {
            refreshBackend();
          } else if (
            typeof event.payload === "string" &&
            event.payload.startsWith("error:")
          ) {
            setBackendOk(false);
          }
        });
      } catch {
        // Not inside Tauri — HTTP polling handles it
      }
    })();
    return () => {
      if (unlisten) unlisten();
    };
  }, [refreshBackend]);

  return (
    <div className="min-h-screen flex text-foreground">
      <aside
        className={cn(
          "hidden md:flex flex-col border-r border-border bg-card/40 backdrop-blur-xl h-screen sticky top-0 z-30 transition-all duration-300",
          open ? "w-64" : "w-[4.5rem]",
        )}
      >
        <div className="h-14 flex items-center gap-2 px-4 border-b border-border/60">
          <Bot className="h-8 w-8 text-primary shrink-0" />
          {open && (
            <div>
              <div className="font-bold leading-tight">norirobotics-mcp</div>
              <div className="text-[10px] text-muted-foreground">Nori A3</div>
            </div>
          )}
        </div>
        <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
          {nav.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                  isActive
                    ? "bg-secondary text-secondary-foreground"
                    : "hover:bg-muted/50",
                  !open && "justify-center px-2",
                )
              }
              title={!open ? label : undefined}
            >
              <Icon className="h-5 w-5 shrink-0" />
              {open && label}
            </NavLink>
          ))}
        </nav>
        <div className="p-2 border-t border-border/60">
          <Button
            variant="ghost"
            className="w-full"
            size="sm"
            onClick={() => setOpen(!open)}
          >
            {open ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </Button>
        </div>
      </aside>

      <div className="md:hidden fixed top-0 left-0 right-0 z-50 h-12 border-b border-border bg-background/90 backdrop-blur flex items-center px-3 gap-2">
        <Button variant="ghost" size="icon" onClick={() => setMobile(!mobile)}>
          <Menu className="h-5 w-5" />
        </Button>
        <span className="font-semibold text-sm">norirobotics-mcp</span>
      </div>
      {mobile && (
        <div className="md:hidden fixed inset-0 z-40 bg-background/95 pt-14 px-3 pb-6 overflow-y-auto">
          {nav.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setMobile(false)}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-3 text-sm mb-1",
                loc.pathname === to ? "bg-secondary" : "hover:bg-muted/50",
              )}
            >
              <Icon className="h-5 w-5" />
              {label}
            </NavLink>
          ))}
        </div>
      )}

      <div className="flex-1 flex flex-col min-w-0 min-h-screen pt-12 md:pt-0">
        <header className="hidden md:flex h-14 items-center border-b border-border/60 px-6 bg-background/40 backdrop-blur-sm sticky top-0 z-20">
          <div className="text-sm text-muted-foreground flex items-center gap-3">
            <span>
              MCP <code className="text-primary">/mcp</code> · API{" "}
              <code className="text-primary">/api</code>
            </span>
            <span
              className="flex items-center gap-1.5"
              data-testid="backend-dot"
            >
              <span
                className={cn(
                  "w-2 h-2 rounded-full animate-pulse",
                  backendOk === null
                    ? "bg-gray-500"
                    : backendOk
                      ? "bg-green-500"
                      : "bg-red-500",
                )}
              />
              {backendOk === null
                ? "Connecting..."
                : backendOk
                  ? "Connected"
                  : "Offline"}
            </span>
            <span
              className={cn(
                "text-sm px-2 py-0.5 rounded-full border",
                activeRobot?.kind === "physical"
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                  : "bg-sky-500/10 text-sky-400 border-sky-500/30",
              )}
              data-testid="robot-kind-badge"
            >
              {activeRobot?.kind === "physical"
                ? `🤖 ${activeRobot.name}`
                : `🖥️ ${activeRobot?.name ?? "Virtual Twin"}`}
            </span>
          </div>
        </header>
        <main className="flex-1 p-4 md:p-6 max-w-6xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
