import { useEffect, useState } from "react";
import { apiGet } from "@/api/client";
import { Card, CardTitle } from "@/components/ui/card";

type Skill = { name?: string; description?: string; id?: string };

export function SkillsPage() {
  const [skills, setSkills] = useState<Skill[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<{ skills: Skill[] }>("/api/skills")
      .then((d) => setSkills(d.skills ?? []))
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  return (
    <div className="space-y-4" data-testid="skills-page">
      <h1 className="text-2xl font-bold">Skills</h1>
      <p className="text-sm text-muted-foreground" data-testid="skills-desc">
        Skills discovered from <code>/api/skills</code>. Chat page loads these
        as system preprompt.
      </p>

      {error && (
        <Card
          className="p-4 border-amber-500/30 bg-amber-500/10"
          data-testid="skills-error"
        >
          <p className="text-sm text-amber-300">
            Failed to load skills: {error}
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

      {skills === null && !error && (
        <Card className="p-8 text-center" data-testid="skills-loading">
          <p className="text-sm text-muted-foreground">Loading skills…</p>
        </Card>
      )}

      {skills !== null && skills.length === 0 && !error && (
        <Card className="p-8 text-center" data-testid="skills-empty">
          <p className="text-sm text-muted-foreground">
            No skills registered yet.
          </p>
          <p className="text-sm text-muted-foreground mt-1">
            This server exposes an empty skill list — not a fake.
          </p>
        </Card>
      )}

      {skills !== null && skills.length > 0 && (
        <div className="grid gap-3" data-testid="skills-list">
          {skills.map((s, i) => (
            <Card key={s.name ?? s.id ?? String(i)} className="p-4">
              <CardTitle className="text-sm">
                {s.name ?? s.id ?? `skill-${i}`}
              </CardTitle>
              {s.description && (
                <p className="text-sm text-muted-foreground mt-1">
                  {s.description}
                </p>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
