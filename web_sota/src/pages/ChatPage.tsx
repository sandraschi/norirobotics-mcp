import { useCallback, useEffect, useRef, useState } from "react";
import { apiGet, apiPost } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useLlmStore } from "@/store/llm";

type ChatMsg = { role: "user" | "assistant"; content: string };

const PERSONALITIES = [
  {
    id: "default",
    label: "Default",
    prompt: "You are a helpful assistant for the Nori A3 robot.",
  },
  {
    id: "concise",
    label: "Concise",
    prompt: "You are concise. Answer in 2-3 sentences.",
  },
  {
    id: "expert",
    label: "Expert",
    prompt:
      "You are a robotics expert. Be technically precise about Nori A3 kinematics and nori-sdk.",
  },
  {
    id: "friendly",
    label: "Friendly",
    prompt:
      "You are friendly and encouraging. Explain like I'm new to robotics.",
  },
  { id: "custom", label: "Custom", prompt: "" },
];

const EXAMPLE_PROMPTS = [
  "What are the Nori A3 specs?",
  "How do I open a mock session?",
  "Show me the fleet peers for Nori",
  "What did Hacker News say about the launch?",
  "Explain the actuator upgrade path",
  "How do I record an episode?",
  "What's the difference between session and episode?",
  "How do I jog the left arm?",
];

const STORAGE_KEY = "chat_history_v1";
const MAX_MSGS = 100;

function loadHistory(): ChatMsg[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const arr = JSON.parse(raw) as ChatMsg[];
    return Array.isArray(arr) ? arr.slice(-MAX_MSGS) : [];
  } catch {
    return [];
  }
}

export function ChatPage() {
  const { provider, model } = useLlmStore();
  const [messages, setMessages] = useState<ChatMsg[]>(() => loadHistory());
  const [input, setInput] = useState("");
  const [personality, setPersonality] = useState("default");
  const [customPrompt, setCustomPrompt] = useState("");
  const [skillPreprompt, setSkillPreprompt] = useState("");
  const [busy, setBusy] = useState(false);
  const [providerStatus, setProviderStatus] = useState<
    "ok" | "offline" | "probing"
  >("probing");
  const listRef = useRef<HTMLDivElement>(null);

  const persist = useCallback((next: ChatMsg[]) => {
    const capped = next.slice(-MAX_MSGS);
    setMessages(capped);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(capped));
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    listRef.current?.scrollTo({
      top: listRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, []);

  useEffect(() => {
    apiGet<{ skills: unknown[] }>("/api/skills")
      .then((d) => {
        if (Array.isArray(d.skills) && d.skills.length > 0) {
          setSkillPreprompt(JSON.stringify(d.skills).slice(0, 4000));
        } else {
          setSkillPreprompt("");
        }
      })
      .catch(() => setSkillPreprompt(""));

    apiGet<{ providers: Record<string, unknown> }>("/api/llm/providers")
      .then((d) => {
        const has = d.providers && Object.keys(d.providers).length > 0;
        setProviderStatus(has ? "ok" : "offline");
      })
      .catch(() => setProviderStatus("offline"));
  }, []);

  const activePersonality = PERSONALITIES.find((p) => p.id === personality);
  const systemPrompt = [
    skillPreprompt ? `Skills: ${skillPreprompt}` : "",
    personality === "custom" ? customPrompt : (activePersonality?.prompt ?? ""),
  ]
    .filter(Boolean)
    .join("\n\n");

  const send = async (text: string = input) => {
    const trimmed = text.trim();
    if (!trimmed || busy) return;
    const userMsg: ChatMsg = { role: "user", content: trimmed };
    const next = [...messages, userMsg];
    persist(next);
    setInput("");
    setBusy(true);
    try {
      const payload = {
        provider,
        model,
        messages: [
          ...(systemPrompt ? [{ role: "system", content: systemPrompt }] : []),
          ...next.map((m) => ({ role: m.role, content: m.content })),
        ],
      };
      const data = await apiPost<{
        choices?: { message?: { content?: string } }[];
        error?: string;
      }>("/api/chat", payload);
      if (data.error) {
        persist([
          ...next,
          { role: "assistant", content: `Error: ${data.error}` },
        ]);
      } else {
        const reply =
          data.choices?.[0]?.message?.content ??
          JSON.stringify(data).slice(0, 2000);
        persist([...next, { role: "assistant", content: reply }]);
      }
    } catch (e) {
      persist([
        ...next,
        {
          role: "assistant",
          content: `Request failed: ${e instanceof Error ? e.message : String(e)}`,
        },
      ]);
    } finally {
      setBusy(false);
    }
  };

  const clear = () => {
    persist([]);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      /* ignore */
    }
  };

  const exportTxt = () => {
    const txt = messages
      .map((m) => `${m.role.toUpperCase()}: ${m.content}`)
      .join("\n\n");
    const blob = new Blob([txt], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "nori-chat.txt";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-4" data-testid="chat-page">
      <h1 className="text-2xl font-bold">Chat</h1>

      <Card
        className="p-3 flex flex-wrap gap-3 items-center"
        data-testid="chat-controls"
      >
        <label className="text-sm flex items-center gap-2">
          Personality
          <select
            data-testid="personality-select"
            className="h-9 rounded-md border border-border bg-secondary px-3 text-sm"
            value={personality}
            onChange={(e) => setPersonality(e.target.value)}
          >
            {PERSONALITIES.map((p) => (
              <option key={p.id} value={p.id}>
                {p.label}
              </option>
            ))}
          </select>
        </label>
        {personality === "custom" && (
          <input
            className="h-9 flex-1 min-w-[200px] rounded-md border border-border bg-secondary px-3 text-sm"
            placeholder="Custom system prompt"
            value={customPrompt}
            onChange={(e) => setCustomPrompt(e.target.value)}
          />
        )}
        <span className="ml-auto flex items-center gap-2 text-sm">
          <span
            className={`w-2 h-2 rounded-full ${providerStatus === "ok" ? "bg-green-500" : providerStatus === "probing" ? "bg-yellow-500 animate-pulse" : "bg-red-500"}`}
          />
          {provider}/{model || "no model"} — {providerStatus}
        </span>
        <Button
          data-testid="chat-export"
          variant="outline"
          size="sm"
          onClick={exportTxt}
          disabled={messages.length === 0}
        >
          Export
        </Button>
        <Button
          data-testid="chat-clear"
          variant="ghost"
          size="sm"
          onClick={clear}
          disabled={messages.length === 0}
        >
          Clear
        </Button>
      </Card>

      <Card>
        <div
          ref={listRef}
          data-testid="chat-messages"
          className="h-[50vh] overflow-auto p-4 space-y-3"
        >
          {messages.length === 0 ? (
            <div className="text-center text-muted-foreground py-12">
              <p className="text-sm">
                Chat with your local LLM about the Nori A3. Skills are loaded as
                system context.
              </p>
              <p className="text-sm mt-2">Try an example prompt below.</p>
            </div>
          ) : (
            messages.map((m) => (
              <div
                key={`${m.role}-${m.content.slice(0, 32)}`}
                className={`rounded-lg px-3 py-2 text-sm ${m.role === "user" ? "bg-primary/10 border border-primary/20" : "bg-muted/40 border border-border"}`}
              >
                <div className="text-sm font-semibold uppercase tracking-wider opacity-60 mb-1">
                  {m.role}
                </div>
                <div className="whitespace-pre-wrap break-words">
                  {m.content}
                </div>
              </div>
            ))
          )}
          {busy && (
            <div className="text-sm text-muted-foreground">Thinking…</div>
          )}
        </div>
        <div className="flex gap-2 p-3 border-t border-border">
          <input
            data-testid="chat-input"
            className="flex-1 h-10 rounded-md border border-border bg-secondary px-3 text-sm"
            placeholder="Ask about Nori A3…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
          />
          <Button
            data-testid="chat-send"
            onClick={() => send()}
            disabled={busy || !input.trim()}
          >
            Send
          </Button>
        </div>
      </Card>

      <div data-testid="example-prompts" className="flex flex-wrap gap-2">
        {EXAMPLE_PROMPTS.map((p) => (
          <button
            key={p}
            type="button"
            onClick={() => send(p)}
            className="text-sm rounded-full border border-border bg-card px-3 py-1 hover:bg-muted transition-colors"
          >
            {p}
          </button>
        ))}
      </div>
    </div>
  );
}
