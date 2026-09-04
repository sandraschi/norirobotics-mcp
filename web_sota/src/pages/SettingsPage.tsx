import { useCallback, useEffect, useState } from "react";
import { apiGet } from "@/api/client";
import { Card, CardTitle } from "@/components/ui/card";
import { useLlmStore } from "@/store/llm";

type ProvidersResponse = {
  providers: Record<string, { url: string; models: string[] }>;
};

export function SettingsPage() {
  const { provider, model, setProvider, setModel } = useLlmStore();
  const [providers, setProviders] = useState<
    Record<string, { url: string; models: string[] }>
  >({});
  const [status, setStatus] = useState<"probing" | "ok" | "offline">("probing");
  const [gpuDetected, setGpuDetected] = useState(false);

  const fetchProviders = useCallback(async () => {
    setStatus("probing");
    try {
      const data = await apiGet<ProvidersResponse>("/api/llm/providers");
      setProviders(data.providers ?? {});
      const hasAny = Object.keys(data.providers ?? {}).length > 0;
      setStatus(hasAny ? "ok" : "offline");
      // auto-select first model if current model not in list
      const currentModels = data.providers?.[provider]?.models ?? [];
      if (
        hasAny &&
        currentModels.length > 0 &&
        !currentModels.includes(model)
      ) {
        setModel(currentModels[0]);
      }
    } catch {
      setProviders({});
      setStatus("offline");
    }
  }, [provider, model, setModel]);

  useEffect(() => {
    fetchProviders();
    // GPU detection via caps probe (best-effort)
    apiGet<{ backend?: string }>("/api/capabilities")
      .then(() => {
        // placeholder: if backend reports gpu, set true; otherwise heuristic false
        setGpuDetected(false);
      })
      .catch(() => setGpuDetected(false));
  }, [fetchProviders]);

  useEffect(() => {
    // when provider changes, refresh model list
    const models = providers[provider]?.models ?? [];
    if (models.length > 0 && !models.includes(model)) {
      setModel(models[0]);
    }
  }, [provider, providers, model, setModel]);

  const models = providers[provider]?.models ?? [];
  const ollamaOk = !!providers.ollama;
  const lmOk = !!providers.lm_studio;

  return (
    <div className="space-y-6" data-testid="settings-page">
      <h1 className="text-2xl font-bold">Settings</h1>

      <Card data-testid="llm-settings-card">
        <CardTitle className="text-base mb-3">
          LLM provider (for the local chat helper)
        </CardTitle>

        <div
          className="flex gap-3 text-sm items-center flex-wrap"
          data-testid="llm-controls"
        >
          <span className="flex items-center gap-2">
            <span
              className={`w-2 h-2 rounded-full ${status === "probing" ? "bg-yellow-500 animate-pulse" : status === "ok" ? "bg-green-500" : "bg-gray-500"}`}
            />
            {status === "probing"
              ? "Probing…"
              : status === "ok"
                ? "LLM detected"
                : "No LLM detected"}
          </span>
          <span
            className={`w-2 h-2 rounded-full ${ollamaOk ? "bg-green-500" : "bg-gray-500"}`}
            title="Ollama :11434"
          />
          Ollama
          <span
            className={`w-2 h-2 rounded-full ${lmOk ? "bg-green-500" : "bg-gray-500"}`}
            title="LM Studio :1234"
          />
          LM Studio
          <button
            type="button"
            className="text-sm text-primary underline ml-2"
            onClick={fetchProviders}
          >
            Refresh
          </button>
        </div>

        <div className="flex gap-3 text-sm mt-4 flex-wrap">
          <select
            data-testid="llm-provider-select"
            className="h-9 rounded-md border border-border bg-secondary px-3"
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
          >
            <option value="ollama">Ollama</option>
            <option value="lm_studio">LM Studio</option>
          </select>

          {models.length > 0 ? (
            <select
              data-testid="llm-model-select"
              className="h-9 flex-1 rounded-md border border-border bg-secondary px-3"
              value={model}
              onChange={(e) => setModel(e.target.value)}
            >
              {models.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          ) : (
            <input
              data-testid="llm-model-select"
              className="h-9 flex-1 rounded-md border border-border bg-secondary px-3"
              placeholder="model name (no provider detected)"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              disabled={status === "offline" && models.length === 0}
            />
          )}
        </div>

        {status === "offline" && (
          <p
            className="text-sm text-muted-foreground mt-3"
            data-testid="llm-offline-hint"
          >
            No local LLM detected on :11434 or :1234. Start Ollama or LM Studio,
            then Refresh. Chat will still work via /api/chat but will return an
            error until a provider is available.
          </p>
        )}

        {gpuDetected && status === "offline" && (
          <p className="text-sm text-amber-300 mt-2" data-testid="gpu-prompt">
            GPU detected but no LLM running — start Ollama for local
            acceleration.
          </p>
        )}
      </Card>

      <Card data-testid="env-card">
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
              Real robot credentials — unset means every session is
              nori_sdk&apos;s own mock
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
