import { useState } from "react";
import {
  Github,
  ChevronDown,
  Sparkles,
  ArrowRight,
  Send,
  Bot,
  User,
  DollarSign,
} from "lucide-react";
import { useNavigate } from "@tanstack/react-router";

export function SetupAndChat() {
  const navigate = useNavigate();

  const [repo, setRepo] = useState("github.com/username/project");
  const [service, setService] = useState("Fullstack App");
  const [location, setLocation] = useState("Southeast Asia");
  const [budget, setBudget] = useState("");

  function handleContinue() {
    navigate({
      to: "/chatbot",
      search: { repo, service, location, budget: budget || "30" },
    });
  }

  return (
    <div className="grid gap-5 lg:grid-cols-[1fr_1.15fr]">
      {/* Quick Setup Form */}
      <div className="glass ring-gradient relative rounded-3xl p-5 shadow-card">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
            <span className="h-2 w-2 rounded-full bg-mint shadow-[0_0_10px_var(--mint)]" />
            Quick Setup
          </div>
          <span className="font-mono text-[10px] text-muted-foreground">step 1 of 2</span>
        </div>

        <h3 className="mt-3 text-xl font-semibold tracking-tight">New Deployment Analysis</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Provide context, then continue with AI Chat.
        </p>

        <div className="mt-5 space-y-4">
          {/* GitHub Repo */}
          <Field label="GitHub Repository URL" icon={<Github className="h-4 w-4" />}>
            <input
              value={repo}
              onChange={(e) => setRepo(e.target.value)}
              placeholder="github.com/username/project"
              className="w-full bg-transparent text-sm font-mono outline-none placeholder:text-muted-foreground"
            />
          </Field>

          {/* Service Type */}
          <Field label="Service Type" icon={<Sparkles className="h-4 w-4" />}>
            <input
              type="text"
              value={service}
              onChange={(e) => setService(e.target.value)}
              placeholder="e.g. Fullstack App"
              className="w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
            />
          </Field>

          {/* Target Location */}
          <Field label="Target Location" icon={<span className="text-xs">🌏</span>}>
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g. Southeast Asia"
              className="w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
            />
          </Field>

          {/* Monthly Budget */}
          <Field label="Monthly Budget (USD)" icon={<DollarSign className="h-4 w-4" />}>
            <input
              type="number"
              min="1"
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
              placeholder="e.g. 30"
              className="w-full bg-transparent text-sm font-mono outline-none placeholder:text-muted-foreground [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
            />
            <span className="shrink-0 text-xs text-muted-foreground">/mo</span>
          </Field>

          <button
            onClick={handleContinue}
            className="group mt-2 flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-primary px-4 py-3 text-sm font-medium text-primary-foreground glow hover:opacity-90 transition"
          >
            Continue with AI Chat
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
          </button>

          <div className="flex items-center justify-between pt-1 text-[11px] text-muted-foreground">
            <span className="font-mono">↳ stack auto-detected</span>
            <span className="flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-cyan animate-pulse-glow" />
              Connected to GitHub
            </span>
          </div>
        </div>
      </div>

      {/* Chatbot Preview */}
      <div className="glass ring-gradient relative overflow-hidden rounded-3xl p-5 shadow-card">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="relative grid h-8 w-8 place-items-center rounded-lg bg-gradient-accent">
              <Bot className="h-4 w-4 text-primary-foreground" />
              <span className="absolute -inset-1 rounded-lg bg-gradient-accent opacity-40 blur-md animate-pulse-glow" />
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

        <div className="mt-4 space-y-3">
          {/* User message */}
          <div className="flex gap-2">
            <div className="grid h-7 w-7 shrink-0 place-items-center rounded-md bg-secondary text-muted-foreground">
              <User className="h-3.5 w-3.5" />
            </div>
            <div className="rounded-2xl rounded-tl-sm border border-glass-border bg-secondary/60 p-3 text-sm">
              I want to deploy this app with a <span className="text-cyan">$30/month</span> budget
              for <span className="text-cyan">20,000 concurrent users</span>. Recommend provider,
              architecture, region, and steps.
            </div>
          </div>

          {/* AI message */}
          <div className="flex gap-2">
            <div className="grid h-7 w-7 shrink-0 place-items-center rounded-md bg-gradient-primary glow">
              <Bot className="h-3.5 w-3.5 text-primary-foreground" />
            </div>
            <div className="space-y-2 rounded-2xl rounded-tl-sm border border-primary/30 bg-primary/5 p-3 text-sm">
              <p>
                Repo detected: <span className="font-mono text-cyan">Next.js</span> +{" "}
                <span className="font-mono text-violet">Golang</span> +{" "}
                <span className="font-mono text-mint">PostgreSQL</span>.
              </p>
              <p>
                <strong>Architecture:</strong> Simple microservice. <strong>Providers:</strong>{" "}
                Vercel (web), Railway/DigitalOcean (api), Supabase/Neon (db).{" "}
                <strong>Region:</strong> Singapore.
              </p>
              <p className="text-destructive/90">
                ⚠ $30/mo may be tight for stable 20k concurrent traffic.
              </p>
            </div>
          </div>

          {/* Result cards */}
          <div className="grid grid-cols-2 gap-2 pt-1">
            <ResultPill label="Architecture" value="Simple Microservice" />
            <ResultPill label="Providers" value="Vercel + Railway + Supabase" />
            <ResultPill label="Region" value="Singapore" />
            <ResultPill label="Resource" value="2 vCPU · 2 GB RAM" />
            <ResultPill label="Type" value="Microservice" />
            <ResultPill label="Risk" value="Budget limitation" tone="warn" />
          </div>

          {/* input */}
          <div className="mt-2 flex items-center gap-2 rounded-2xl border border-glass-border bg-background/40 p-2">
            <input
              placeholder="Describe your deployment goal, budget, traffic..."
              className="w-full bg-transparent px-2 text-sm outline-none placeholder:text-muted-foreground"
            />
            <button
              onClick={handleContinue}
              className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-primary glow"
            >
              <Send className="h-4 w-4 text-primary-foreground" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function Field({
  label,
  icon,
  children,
}: {
  label: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
        {label}
      </span>
      <div className="flex items-center gap-2 rounded-xl border border-glass-border bg-background/40 px-3 py-2.5 focus-within:border-primary/60 transition">
        <span className="text-muted-foreground">{icon}</span>
        {children}
      </div>
    </label>
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
