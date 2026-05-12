import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, useRef, useEffect } from "react";
import {
  Bot,
  User,
  Send,
  ArrowLeft,
  Rocket,
  DollarSign,
  Zap,
  CheckCircle,
  XCircle,
} from "lucide-react";
import { z } from "zod";
import { analyzeDeployment, sendFollowUp } from "@/api/chat-handler";

// ── Route Definition ──────────────────────────────────────────────────────────

const searchSchema = z.object({
  repo: z.coerce.string().optional().default("github.com/username/project"),
  service: z.coerce.string().optional().default("Fullstack App"),
  location: z.coerce.string().optional().default("Southeast Asia"),
  budget: z.coerce.string().optional().default("30"),
});

export const Route = createFileRoute("/chatbot")({
  validateSearch: searchSchema,
  component: ChatbotPage,
});

// ── Types ─────────────────────────────────────────────────────────────────────

interface Message {
  role: "user" | "ai";
  content: string;
  pills?: Pill[];
  isTyping?: boolean;
}

interface Pill {
  label: string;
  value: string;
  tone?: "warn";
}

interface CostBreakdownItem {
  item: string;
  cost: string;
}

interface Alternative {
  provider: string;
  architecture: string;
  monthly_estimate: string;
  pros: string[];
  cons: string[];
  best_for: string;
}

interface Recommendation {
  stack_detected: string[];
  architecture: string;
  providers: string;
  region: string;
  resources: string;
  deployment_type: string;
  risk: string;
  risk_level: "low" | "medium" | "high";
  summary: string;
  warning: string | null;
  estimated_cost?: {
    monthly_min: number;
    monthly_max: number;
    currency: string;
    breakdown: CostBreakdownItem[];
    within_budget: boolean;
    budget_note: string;
  };
  alternatives?: Alternative[];
  feasibility: {
    budget: number;
    scalability: number;
    reliability: number;
    ease_of_setup: number;
  };
}

// ── Constants ─────────────────────────────────────────────────────────────────

const REGION_MAP: Record<string, string> = {
  "Southeast Asia": "Singapore",
  "US East": "N. Virginia",
  "US West": "Oregon",
  "Europe West": "Ireland",
  "Asia Pacific NE": "Tokyo",
  Australia: "Sydney",
};

const SCORE_COLORS: Record<string, string> = {
  budget: "bg-primary",
  scalability: "bg-cyan",
  reliability: "bg-mint",
  ease_of_setup: "bg-violet",
};

// ── Component ─────────────────────────────────────────────────────────────────

function ChatbotPage() {
  const { repo, service, location, budget } = Route.useSearch();
  const navigate = useNavigate();

  const region = REGION_MAP[location] ?? "Singapore";
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputVal, setInputVal] = useState("");
  const [rec, setRec] = useState<Recommendation | null>(null);
  const [loading, setLoading] = useState(false);
  const [sidebarReady, setSidebarReady] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // ── FIX: guard against React StrictMode double-invoke ──────────────────────
  const hasRun = useRef(false);

  useEffect(() => {
    if (hasRun.current) return;
    hasRun.current = true;

    const firstMsg: Message = {
      role: "user",
      content: `I want to deploy ${repo} as a ${service} targeting ${location} with a monthly budget of $${budget} USD. Recommend provider, architecture, region, and deployment steps.`,
    };
    setMessages([firstMsg]);
    generateRecommendation(firstMsg.content);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ── API Call ────────────────────────────────────────────────────────────────

  async function generateRecommendation(userMessage: string) {
    setLoading(true);
    addTypingIndicator();

    try {
      // Pass budget to analyzeDeployment
      const raw = await analyzeDeployment(repo, service, location, budget, userMessage);
      const clean = raw.replace(/```json|```/g, "").trim();
      const parsed: Recommendation = JSON.parse(clean);
      setRec(parsed);

      const pills: Pill[] = [
        { label: "Architecture", value: parsed.architecture },
        { label: "Providers", value: parsed.providers },
        { label: "Region", value: parsed.region },
        { label: "Resources", value: parsed.resources },
        { label: "Type", value: parsed.deployment_type },
        {
          label: "Risk",
          value: parsed.risk,
          tone: parsed.risk_level !== "low" ? "warn" : undefined,
        },
      ];

      const stackTags = (parsed.stack_detected ?? []).join(" + ") || "Unknown stack";

      const costLine = parsed.estimated_cost
        ? `\n\n💰 Estimated cost: <span class="text-mint font-semibold">$${parsed.estimated_cost.monthly_min}–$${parsed.estimated_cost.monthly_max}/mo</span> · ${parsed.estimated_cost.budget_note}`
        : "";

      const aiText = `Repo analyzed. Stack detected: ${stackTags}.\n\n${parsed.summary}${costLine}${parsed.warning ? `\n\n⚠ ${parsed.warning}` : ""}`;

      const plainCostLine = parsed.estimated_cost
        ? `\n\nEstimated cost: $${parsed.estimated_cost.monthly_min}-${parsed.estimated_cost.monthly_max}/mo. ${parsed.estimated_cost.budget_note}`
        : "";
      const plainAiText = `Repo analyzed. Stack detected: ${stackTags}.\n\n${parsed.summary}${plainCostLine}${parsed.warning ? `\n\nWarning: ${parsed.warning}` : ""}`;

      removeTypingIndicator();
      setMessages((prev) => [...prev, { role: "ai", content: plainAiText, pills }]);
      setSidebarReady(true);
    } catch (error) {
      removeTypingIndicator();
      console.error("Error generating recommendation:", error);
      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          content: "Sorry, I couldn't generate a recommendation. Please try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function sendFollowUpMessage() {
    const text = inputVal.trim();
    if (!text || loading) return;
    setInputVal("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);
    addTypingIndicator();

    try {
      const reply = await sendFollowUp(text, {
        repo,
        service,
        region,
        budget,
        previousAnalysis: rec ? { ...rec } : undefined,
      });
      removeTypingIndicator();
      setMessages((prev) => [...prev, { role: "ai", content: reply }]);
    } catch (error) {
      removeTypingIndicator();
      console.error("Follow-up error:", error);
      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          content: "Sorry, I couldn't generate a response. Please try again.",
        },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  // ── Typing Helpers ──────────────────────────────────────────────────────────

  function addTypingIndicator() {
    setMessages((prev) => [...prev, { role: "ai", content: "", isTyping: true }]);
  }

  function removeTypingIndicator() {
    setMessages((prev) => prev.filter((m) => !m.isTyping));
  }

  // ── Render ──────────────────────────────────────────────────────────────────

  return (
    <div className="relative flex min-h-screen flex-col overflow-hidden bg-hero">
      {/* Ambient blobs */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 left-1/3 h-[40rem] w-[40rem] rounded-full bg-primary/20 blur-[140px]" />
        <div className="absolute top-[40%] -right-40 h-[36rem] w-[36rem] rounded-full bg-violet/20 blur-[140px]" />
        <div className="absolute bottom-0 -left-40 h-[30rem] w-[30rem] rounded-full bg-cyan/15 blur-[140px]" />
      </div>

      {/* ── Navbar ── */}
      <header className="relative z-50 px-4 pt-4">
        <nav className="glass mx-auto flex max-w-6xl items-center justify-between rounded-2xl px-4 py-2.5 shadow-card">
          <a href="/" className="flex items-center gap-2">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-primary glow">
              <Rocket className="h-4 w-4 text-primary-foreground" />
            </span>
            <span className="font-semibold tracking-tight">DeployBuddy</span>
          </a>

          {/* Context pills */}
          <div className="hidden items-center gap-2 md:flex">
            <CtxPill label="REPO" value={repo.replace("github.com/", "")} />
            <CtxPill label="TYPE" value={service} />
            <CtxPill label="REGION" value={region} />
            <CtxPill label="BUDGET" value={`$${budget}/mo`} />
          </div>

          <button
            onClick={() => navigate({ to: "/" })}
            className="flex items-center gap-1.5 rounded-xl border border-glass-border bg-glass px-3 py-1.5 text-xs text-muted-foreground transition hover:border-primary/40 hover:text-foreground"
          >
            <ArrowLeft className="h-3 w-3" />
            New Analysis
          </button>
        </nav>
      </header>

      {/* ── Main ── */}
      <main className="relative z-10 flex flex-1 gap-4 px-4 pb-4 pt-4">
        <div className="mx-auto flex w-full max-w-6xl gap-4">
          {/* ── Messages Panel ── */}
          <div className="glass ring-gradient flex flex-1 flex-col overflow-hidden rounded-3xl shadow-card">
            {/* Chat header */}
            <div className="flex items-center justify-between border-b border-glass-border px-5 py-4">
              <div className="flex items-center gap-3">
                <div className="relative grid h-9 w-9 place-items-center rounded-xl bg-gradient-primary glow">
                  <Bot className="h-5 w-5 text-primary-foreground" />
                  <span className="absolute -inset-1 rounded-xl bg-gradient-primary opacity-30 blur-md animate-pulse-glow" />
                </div>
                <div>
                  <p className="text-sm font-semibold leading-tight">DeployBuddy AI</p>
                  <p className="font-mono text-[10px] text-muted-foreground">
                    deployment-advisor · v2026.1
                  </p>
                </div>
              </div>
              <span className="rounded-full border border-glass-border bg-glass px-2 py-0.5 font-mono text-[10px] text-mint">
                ● live
              </span>
            </div>

            {/* Messages */}
            <div className="flex-1 space-y-4 overflow-y-auto px-5 py-5 scrollbar-thin scrollbar-track-transparent scrollbar-thumb-glass-border">
              {messages.map((msg, i) => (
                <MessageRow key={i} msg={msg} />
              ))}
              <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div className="border-t border-glass-border px-4 py-3">
              <div className="flex items-center gap-2 rounded-2xl border border-glass-border bg-background/40 p-2">
                <input
                  ref={inputRef}
                  value={inputVal}
                  onChange={(e) => setInputVal(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && sendFollowUpMessage()}
                  placeholder="Ask about budget, scaling, CI/CD, alternatives..."
                  className="w-full bg-transparent px-2 text-sm outline-none placeholder:text-muted-foreground"
                  disabled={loading}
                />
                <button
                  onClick={sendFollowUpMessage}
                  disabled={loading || !inputVal.trim()}
                  className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-gradient-primary glow transition hover:opacity-90 disabled:opacity-40"
                >
                  <Send className="h-4 w-4 text-primary-foreground" />
                </button>
              </div>
            </div>
          </div>

          {/* ── Sidebar ── */}
          {sidebarReady && rec && (
            <aside className="hidden w-72 shrink-0 flex-col gap-3 lg:flex overflow-y-auto max-h-[calc(100vh-6rem)] scrollbar-thin scrollbar-track-transparent scrollbar-thumb-glass-border">
              {/* Recommendation card */}
              <div className="glass ring-gradient rounded-3xl p-4 shadow-card">
                <p className="mb-3 font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                  📦 Recommendation
                </p>
                <div className="space-y-2">
                  <SbItem label="Architecture" value={rec.architecture} />
                  <SbItem label="Providers" value={rec.providers} />
                  <SbItem label="Region" value={rec.region} />
                  <SbItem label="Resources" value={rec.resources} />
                  <SbItem label="Type" value={rec.deployment_type} />
                  <SbItem
                    label="Risk"
                    value={rec.risk}
                    tone={rec.risk_level !== "low" ? "warn" : undefined}
                  />
                </div>
              </div>

              {/* Estimated Cost card */}
              {rec.estimated_cost && (
                <div className="glass ring-gradient rounded-3xl p-4 shadow-card">
                  <p className="mb-3 font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                    💰 Estimated Cost
                  </p>
                  <div className="mb-3 flex items-end justify-between">
                    <div>
                      <p className="text-xl font-bold text-mint">
                        ${rec.estimated_cost.monthly_min}–${rec.estimated_cost.monthly_max}
                        <span className="text-xs font-normal text-muted-foreground">/mo</span>
                      </p>
                      <p className="mt-0.5 text-[10px] text-muted-foreground">
                        Budget: ${budget}/mo
                      </p>
                    </div>
                    <span
                      className={`flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                        rec.estimated_cost.within_budget
                          ? "bg-mint/10 text-mint border border-mint/30"
                          : "bg-destructive/10 text-destructive border border-destructive/30"
                      }`}
                    >
                      {rec.estimated_cost.within_budget ? (
                        <>
                          <CheckCircle className="h-2.5 w-2.5" /> Within budget
                        </>
                      ) : (
                        <>
                          <XCircle className="h-2.5 w-2.5" /> Over budget
                        </>
                      )}
                    </span>
                  </div>
                  <p className="mb-3 text-[10px] text-muted-foreground">
                    {rec.estimated_cost.budget_note}
                  </p>
                  <div className="space-y-1.5 border-t border-glass-border pt-3">
                    {rec.estimated_cost.breakdown.map((item, i) => (
                      <div key={i} className="flex items-center justify-between">
                        <span className="text-[10px] text-muted-foreground">{item.item}</span>
                        <span className="font-mono text-[10px] text-foreground">{item.cost}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Provider Comparison card */}
              {rec.alternatives && rec.alternatives.length > 0 && (
                <div className="glass ring-gradient rounded-3xl p-4 shadow-card">
                  <p className="mb-3 font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                    ⚡ Provider Comparison
                  </p>
                  <div className="space-y-3">
                    {rec.alternatives.map((alt, i) => (
                      <AlternativeCard key={i} alt={alt} />
                    ))}
                  </div>
                </div>
              )}

              {/* Feasibility scores */}
              <div className="glass ring-gradient rounded-3xl p-4 shadow-card">
                <p className="mb-3 font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                  📊 Feasibility
                </p>
                <div className="space-y-3">
                  {(
                    [
                      ["budget", "Budget fit"],
                      ["scalability", "Scalability"],
                      ["reliability", "Reliability"],
                      ["ease_of_setup", "Setup ease"],
                    ] as const
                  ).map(([key, label]) => (
                    <ScoreBar
                      key={key}
                      label={label}
                      value={rec.feasibility[key]}
                      colorClass={SCORE_COLORS[key]}
                    />
                  ))}
                </div>
              </div>
            </aside>
          )}
        </div>
      </main>
    </div>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────

function MessageRow({ msg }: { msg: Message }) {
  if (msg.isTyping) {
    return (
      <div className="flex gap-2">
        <AiAvatar />
        <div className="flex items-center gap-1 rounded-2xl rounded-tl-sm border border-primary/20 bg-primary/5 px-4 py-3">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="h-1.5 w-1.5 animate-bounce rounded-full bg-violet"
              style={{ animationDelay: `${i * 0.15}s` }}
            />
          ))}
        </div>
      </div>
    );
  }

  if (msg.role === "user") {
    return (
      <div className="flex justify-end gap-2">
        <div className="max-w-[75%] rounded-2xl rounded-tr-sm border border-primary/20 bg-primary/10 px-4 py-2.5 text-sm leading-relaxed">
          {msg.content}
        </div>
        <div className="grid h-7 w-7 shrink-0 place-items-center rounded-md bg-secondary text-muted-foreground">
          <User className="h-3.5 w-3.5" />
        </div>
      </div>
    );
  }

  // AI message
  return (
    <div className="flex gap-2">
      <AiAvatar />
      <div className="flex-1 space-y-3">
        <div className="whitespace-pre-line rounded-2xl rounded-tl-sm border border-primary/20 bg-primary/5 px-4 py-3 text-sm leading-relaxed">
          {msg.content}
        </div>
        {msg.pills && msg.pills.length > 0 && (
          <div className="grid grid-cols-2 gap-2">
            {msg.pills.map((p) => (
              <ResultPill key={p.label} label={p.label} value={p.value} tone={p.tone} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function AiAvatar() {
  return (
    <div className="grid h-7 w-7 shrink-0 place-items-center rounded-md bg-gradient-primary glow">
      <Bot className="h-3.5 w-3.5 text-primary-foreground" />
    </div>
  );
}

function CtxPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center gap-1.5 rounded-lg border border-glass-border bg-glass px-2.5 py-1">
      <span className="font-mono text-[9px] font-semibold uppercase tracking-widest text-muted-foreground">
        {label}
      </span>
      <span className="font-mono text-[10px] text-cyan">{value}</span>
    </div>
  );
}

function SbItem({ label, value, tone }: { label: string; value: string; tone?: "warn" }) {
  return (
    <div
      className={`rounded-xl border p-2.5 ${
        tone === "warn"
          ? "border-destructive/30 bg-destructive/5"
          : "border-glass-border bg-background/30"
      }`}
    >
      <p className="text-[9.5px] font-semibold uppercase tracking-wider text-muted-foreground">
        {label}
      </p>
      <p className={`mt-0.5 text-xs font-medium ${tone === "warn" ? "text-destructive" : ""}`}>
        {value}
      </p>
    </div>
  );
}

function ResultPill({ label, value, tone }: { label: string; value: string; tone?: "warn" }) {
  return (
    <div
      className={`rounded-xl border p-2.5 ${
        tone === "warn" ? "border-destructive/40 bg-destructive/5" : "border-glass-border bg-glass"
      }`}
    >
      <p className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</p>
      <p className={`mt-0.5 text-xs font-medium ${tone === "warn" ? "text-destructive" : ""}`}>
        {value}
      </p>
    </div>
  );
}

function AlternativeCard({ alt }: { alt: Alternative }) {
  return (
    <div className="rounded-xl border border-glass-border bg-background/30 p-3">
      <div className="mb-2 flex items-center justify-between">
        <p className="text-xs font-semibold">{alt.provider}</p>
        <span className="font-mono text-[10px] text-cyan">{alt.monthly_estimate}</span>
      </div>
      <p className="mb-2 text-[10px] text-muted-foreground">{alt.architecture}</p>
      <div className="mb-2 space-y-0.5">
        {alt.pros.map((p, i) => (
          <div key={i} className="flex items-start gap-1">
            <CheckCircle className="mt-0.5 h-2.5 w-2.5 shrink-0 text-mint" />
            <span className="text-[10px] text-foreground/80">{p}</span>
          </div>
        ))}
        {alt.cons.map((c, i) => (
          <div key={i} className="flex items-start gap-1">
            <XCircle className="mt-0.5 h-2.5 w-2.5 shrink-0 text-destructive/70" />
            <span className="text-[10px] text-muted-foreground">{c}</span>
          </div>
        ))}
      </div>
      <div className="rounded-lg bg-violet/10 px-2 py-1">
        <span className="text-[9px] text-violet">Best for: {alt.best_for}</span>
      </div>
    </div>
  );
}

function ScoreBar({
  label,
  value,
  colorClass,
}: {
  label: string;
  value: number;
  colorClass: string;
}) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between">
        <span className="text-[11px] text-muted-foreground">{label}</span>
        <span className="font-mono text-[10px] text-muted-foreground">{value}%</span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-background/40">
        <div
          className={`h-full rounded-full ${colorClass} transition-all duration-700`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}
