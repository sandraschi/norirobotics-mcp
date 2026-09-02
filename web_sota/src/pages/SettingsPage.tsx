import { Card, CardTitle } from "@/components/ui/card";
import { useLlmStore } from "@/store/llm";

export function SettingsPage() {
  const { provider, model, setProvider, setModel } = useLlmStore();

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      <Card>
        <CardTitle className="text-base mb-3">
          LLM provider (for the local chat helper)
        </CardTitle>
        <div className="flex gap-3 text-sm">
          <select
            data-testid="llm-provider-select"
            className="h-9 rounded-md border border-border bg-secondary px-3"
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
          >
            <option value="ollama">Ollama</option>
            <option value="lm_studio">LM Studio</option>
          </select>
          <input
            data-testid="llm-model-select"
            className="h-9 flex-1 rounded-md border border-border bg-secondary px-3"
            placeholder="model name"
            value={model}
            onChange={(e) => setModel(e.target.value)}
          />
        </div>
      </Card>

      <Card>
        <CardTitle className="text-base mb-3">Environment</CardTitle>
        <dl className="text-sm space-y-2 font-mono">
          <div>
            <dt className="text-muted-foreground">
              NORI_MCP_HOST / NORI_MCP_PORT
            </dt>
            <dd>Backend bind (default 127.0.0.1:11970)</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">
              NORI_MCP_SUPABASE_URL / NORI_MCP_SUPABASE_ANON_KEY /
              NORI_MCP_ROBOT_ROOM
            </dt>
            <dd>
              Real robot credentials — unset means every session is nori_sdk's
              own mock
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">
              NORI_MCP_USER_EMAIL / NORI_MCP_USER_PASSWORD
            </dt>
            <dd>Nori account auth for UserAuth token refresh</dd>
          </div>
        </dl>
      </Card>
    </div>
  );
}
