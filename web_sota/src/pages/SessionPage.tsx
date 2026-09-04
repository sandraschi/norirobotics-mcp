import { useCallback, useEffect, useState } from "react";
import { apiDelete, apiGet, apiPost } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";

type SessionStatus = {
  success: boolean;
  connected: boolean;
  mock?: boolean;
  robot_kind?: "physical" | "virtual" | "unknown";
  profile_name?: string | null;
  message?: string;
  status?: unknown;
  telemetry?: unknown;
  camera_layout?: unknown;
};

type RobotProfile = {
  id: string;
  name: string;
  kind: "physical" | "virtual";
  supabase_url: string;
  supabase_anon_key: string;
  robot_room: string;
  user_email: string;
  user_password: string;
};

type ProfilesResponse = { profiles: RobotProfile[]; active_id: string };

const emptyForm = {
  name: "",
  kind: "virtual" as "physical" | "virtual",
  supabase_url: "",
  supabase_anon_key: "",
  robot_room: "",
  user_email: "",
  user_password: "",
};

export function SessionPage() {
  const [status, setStatus] = useState<SessionStatus | null>(null);
  const [profiles, setProfiles] = useState<RobotProfile[]>([]);
  const [activeId, setActiveId] = useState<string>("virtual");
  const [busy, setBusy] = useState(false);
  const [profileBusy, setProfileBusy] = useState<string | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [formOpen, setFormOpen] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [testing, setTesting] = useState(false);

  const refresh = useCallback(() => {
    apiGet<SessionStatus>("/api/session")
      .then(setStatus)
      .catch(() => setStatus(null));
    apiGet<ProfilesResponse>("/api/robot-profiles")
      .then((d) => {
        setProfiles(d.profiles);
        setActiveId(d.active_id);
      })
      .catch(() => undefined);
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

  const activateProfile = async (id: string) => {
    setProfileBusy(id);
    try {
      await apiPost(`/api/robot-profiles/${encodeURIComponent(id)}/activate`);
      refresh();
    } finally {
      setProfileBusy(null);
    }
  };

  const removeProfile = async (id: string) => {
    setProfileBusy(id);
    try {
      await apiDelete(`/api/robot-profiles/${encodeURIComponent(id)}`);
      refresh();
    } catch (e) {
      window.alert(
        e instanceof Error ? e.message : "Could not remove profile.",
      );
    } finally {
      setProfileBusy(null);
    }
  };

  const submitProfile = async () => {
    setFormError(null);
    if (!form.name.trim()) {
      setFormError("Name is required.");
      return;
    }
    if (
      form.kind === "physical" &&
      !(
        form.supabase_url.trim() &&
        form.supabase_anon_key.trim() &&
        form.robot_room.trim()
      )
    ) {
      setFormError(
        "Physical profiles need Supabase URL, anon key, and robot room.",
      );
      return;
    }
    setTesting(form.kind === "physical");
    try {
      await apiPost("/api/robot-profiles", form);
      setForm(emptyForm);
      setFormOpen(false);
      refresh();
    } catch (e) {
      setFormError(e instanceof Error ? e.message : "Could not add profile.");
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="session-page">
      <h1 className="text-2xl font-bold">Session</h1>

      <Card data-testid="session-connection">
        <div className="flex items-center justify-between mb-3">
          <CardTitle>Connection</CardTitle>
          <span
            className={`text-sm px-2 py-0.5 rounded-full ${
              status?.connected
                ? "bg-green-500/10 text-green-400 border border-green-500/30"
                : "bg-muted text-muted-foreground border border-border"
            }`}
          >
            {status?.connected
              ? status.robot_kind === "physical"
                ? `connected — physical (${status.profile_name})`
                : `connected — virtual (${status.profile_name ?? "mock"})`
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
        {!status?.connected && (
          <p className="text-sm text-muted-foreground mt-3">
            Connecting will use the active profile below (
            <strong>
              {profiles.find((p) => p.id === activeId)?.name ?? "Virtual Twin"}
            </strong>
            ).
          </p>
        )}
      </Card>

      <Card data-testid="session-profiles">
        <div className="flex items-center justify-between mb-3">
          <CardTitle>Robot Profiles</CardTitle>
          <Button
            size="sm"
            variant="outline"
            onClick={() => setFormOpen((v) => !v)}
          >
            {formOpen ? "Cancel" : "Add Profile"}
          </Button>
        </div>

        <div className="space-y-2">
          {profiles.map((p) => (
            <div
              key={p.id}
              className="flex items-center justify-between rounded-lg border border-border p-3"
            >
              <div className="flex items-center gap-3">
                <span
                  className={`text-sm px-2 py-0.5 rounded-full ${
                    p.kind === "physical"
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                      : "bg-sky-500/10 text-sky-400 border border-sky-500/30"
                  }`}
                >
                  {p.kind === "physical" ? "🤖 physical" : "🖥️ virtual"}
                </span>
                <div>
                  <div className="text-sm font-medium">{p.name}</div>
                  {p.kind === "physical" && (
                    <div className="text-sm text-muted-foreground">
                      {p.robot_room}
                    </div>
                  )}
                </div>
                {p.id === activeId && (
                  <span className="text-[10px] uppercase tracking-wider text-primary">
                    active
                  </span>
                )}
              </div>
              <div className="flex gap-2">
                {p.id !== activeId && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => activateProfile(p.id)}
                    disabled={profileBusy === p.id}
                  >
                    Activate
                  </Button>
                )}
                {p.id !== "virtual" && p.id !== activeId && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => removeProfile(p.id)}
                    disabled={profileBusy === p.id}
                  >
                    Remove
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>

        {formOpen && (
          <div className="mt-4 space-y-3 border-t border-border pt-4">
            <div className="grid gap-2 sm:grid-cols-2">
              <label className="text-sm">
                Name
                <input
                  className="mt-1 w-full rounded-md border border-border bg-background px-3 py-1.5 text-sm"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="e.g. Mr. Li's A3"
                />
              </label>
              <label className="text-sm">
                Kind
                <select
                  className="mt-1 w-full rounded-md border border-border bg-background px-3 py-1.5 text-sm"
                  value={form.kind}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      kind: e.target.value as "physical" | "virtual",
                    })
                  }
                >
                  <option value="virtual">Virtual Twin (no hardware)</option>
                  <option value="physical">Physical A3 (real robot)</option>
                </select>
              </label>
            </div>

            {form.kind === "physical" && (
              <div className="grid gap-2 sm:grid-cols-2">
                <label className="text-sm sm:col-span-2">
                  Supabase URL
                  <input
                    className="mt-1 w-full rounded-md border border-border bg-background px-3 py-1.5 text-sm"
                    value={form.supabase_url}
                    onChange={(e) =>
                      setForm({ ...form, supabase_url: e.target.value })
                    }
                    placeholder="https://xxxx.supabase.co"
                  />
                </label>
                <label className="text-sm sm:col-span-2">
                  Supabase anon key
                  <input
                    type="password"
                    className="mt-1 w-full rounded-md border border-border bg-background px-3 py-1.5 text-sm"
                    value={form.supabase_anon_key}
                    onChange={(e) =>
                      setForm({ ...form, supabase_anon_key: e.target.value })
                    }
                  />
                </label>
                <label className="text-sm">
                  Robot room
                  <input
                    className="mt-1 w-full rounded-md border border-border bg-background px-3 py-1.5 text-sm"
                    value={form.robot_room}
                    onChange={(e) =>
                      setForm({ ...form, robot_room: e.target.value })
                    }
                    placeholder="NORI-A3-0001"
                  />
                </label>
                <label className="text-sm">
                  Account email (optional)
                  <input
                    className="mt-1 w-full rounded-md border border-border bg-background px-3 py-1.5 text-sm"
                    value={form.user_email}
                    onChange={(e) =>
                      setForm({ ...form, user_email: e.target.value })
                    }
                  />
                </label>
                <label className="text-sm sm:col-span-2">
                  Account password (optional)
                  <input
                    type="password"
                    className="mt-1 w-full rounded-md border border-border bg-background px-3 py-1.5 text-sm"
                    value={form.user_password}
                    onChange={(e) =>
                      setForm({ ...form, user_password: e.target.value })
                    }
                  />
                </label>
              </div>
            )}

            {formError && <p className="text-sm text-red-400">{formError}</p>}
            {testing && (
              <p className="text-sm text-muted-foreground">
                Testing connection live against the robot — this can take up to
                15s...
              </p>
            )}

            <Button onClick={submitProfile} disabled={testing}>
              {form.kind === "physical"
                ? "Test & Save Profile"
                : "Save Profile"}
            </Button>
          </div>
        )}
      </Card>

      {status?.connected && (
        <Card data-testid="session-telemetry">
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
    </div>
  );
}
