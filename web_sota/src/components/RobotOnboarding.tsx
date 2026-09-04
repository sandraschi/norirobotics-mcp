import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiGet } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";

type RobotProfile = { id: string; name: string; kind: "physical" | "virtual" };
type ProfilesResponse = { profiles: RobotProfile[]; active_id: string };

/** Shown on the Dashboard whenever no physical A3 has ever been registered - session-
 * only dismissal (component state, not localStorage): this should reappear on a fresh
 * visit rather than nag-once-then-vanish-forever, since the whole point is making sure
 * "physical vs Virtual Twin" stays visible, not just shown on day one. */
export function RobotOnboarding() {
  const [profiles, setProfiles] = useState<RobotProfile[] | null>(null);
  const [dismissed, setDismissed] = useState(false);
  const navigate = useNavigate();

  const refresh = useCallback(() => {
    apiGet<ProfilesResponse>("/api/robot-profiles")
      .then((d) => setProfiles(d.profiles))
      .catch(() => setProfiles(null));
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  if (dismissed || !profiles) return null;
  const hasPhysical = profiles.some((p) => p.kind === "physical");
  if (hasPhysical) return null;

  return (
    <Card className="border-amber-500/30 bg-amber-500/5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <CardTitle className="mb-1">Have a physical Nori A3?</CardTitle>
          <p className="text-sm text-muted-foreground">
            Right now every tool call runs against the Virtual Twin (nori_sdk's
            mock). If a real A3 is powered on somewhere — yours, or someone
            else's you have Supabase credentials for — register it as a named
            profile so it's unambiguous which robot produced a given session or
            recording.
          </p>
        </div>
      </div>
      <div className="flex gap-2 mt-3">
        <Button size="sm" onClick={() => navigate("/session")}>
          Yes, set it up
        </Button>
        <Button size="sm" variant="ghost" onClick={() => setDismissed(true)}>
          Not yet — keep using Virtual Twin
        </Button>
      </div>
    </Card>
  );
}
