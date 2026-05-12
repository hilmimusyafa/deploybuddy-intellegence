import { useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import {
  AlertTriangle,
  Boxes,
  Bot,
  Cpu,
  DollarSign,
  FileCode2,
  Globe,
  GitBranch,
  LayoutDashboard,
  MessageSquare,
  PackageSearch,
  Rocket,
  Settings,
  ShieldCheck,
  Sparkles,
  TerminalSquare,
  Zap,
  Check,
  ArrowRight,
  Database,
  Cloud,
  Github,
  Server,
  Send,
  User,
  ChevronRight,
  Eye,
  EyeOff,
  Key,
  Plus,
  Trash2,
} from "lucide-react";

/* ------------------------------- Section UI ------------------------------- */

function SectionTag({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-glass-border bg-glass px-3 py-1 font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
      <span className="h-1.5 w-1.5 rounded-full bg-cyan animate-pulse-glow" />
      {children}
    </span>
  );
}

function SectionHeader({ tag, title, sub }: { tag: string; title: React.ReactNode; sub?: string }) {
  return (
    <div className="mx-auto max-w-3xl text-center">
      <SectionTag>{tag}</SectionTag>
      <h2 className="mt-4 text-balance text-3xl font-semibold tracking-tight md:text-5xl">
        {title}
      </h2>
      {sub && <p className="mx-auto mt-4 max-w-2xl text-pretty text-muted-foreground">{sub}</p>}
    </div>
  );
}

/* ------------------------------- Problem ---------------------------------- */

const pains = [
  {
    icon: Boxes,
    t: "Provider overload",
    d: "AWS, Vercel, Railway, Supabase, DO… which one for what?",
  },
  {
    icon: Cpu,
    t: "Resource guesswork",
    d: "Unsure how much CPU, RAM, storage, and DB capacity you need.",
  },
  {
    icon: DollarSign,
    t: "Hidden cloud costs",
    d: "Pricing pages and egress fees are hard to estimate.",
  },
  {
    icon: Globe,
    t: "Region confusion",
    d: "Picking the right region for your users isn't obvious.",
  },
  {
    icon: TerminalSquare,
    t: "Setup friction",
    d: "Docker, env vars, CI/CD and provider configs trip up beginners.",
  },
  {
    icon: PackageSearch,
    t: "Scattered docs",
    d: "Documentation lives in a dozen different places.",
  },
];

export function Problem() {
  return (
    <section className="relative py-24">
      <SectionHeader
        tag="The problem"
        title={
          <>
            Deployment decisions are{" "}
            <span className="text-gradient">harder than writing code.</span>
          </>
        }
        sub="You shipped the feature. Now you have to choose a stack, a provider, a region, a plan, and figure out what it'll cost."
      />
      <div className="mx-auto mt-12 grid max-w-6xl gap-4 px-4 sm:grid-cols-2 lg:grid-cols-3">
        {pains.map((p) => (
          <div key={p.t} className="glass rounded-2xl p-5 transition hover:border-primary/40">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-secondary text-cyan">
              <p.icon className="h-5 w-5" />
            </div>
            <h3 className="mt-4 font-semibold">{p.t}</h3>
            <p className="mt-1 text-sm text-muted-foreground">{p.d}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

/* --------------------------- Chatbot-first flow --------------------------- */

const flowSteps = [
  { icon: Github, label: "Repository" },
  { icon: Sparkles, label: "Service Type" },
  { icon: Globe, label: "Location" },
  { icon: MessageSquare, label: "AI Chat Prompt" },
  { icon: Rocket, label: "Recommendation" },
];

export function ChatbotFirst() {
  return (
    <section className="relative py-24">
      <SectionHeader
        tag="Chatbot-first"
        title={
          <>
            Tell DeployBuddy <span className="text-gradient-accent">what you want to deploy.</span>
          </>
        }
        sub="The form only collects the minimum. The chatbot collects your real intent and generates the final answer."
      />

      <div className="mx-auto mt-14 max-w-6xl px-4">
        <div className="glass ring-gradient relative rounded-3xl p-6 md:p-10">
          <div className="flex flex-wrap items-center justify-between gap-4">
            {flowSteps.map((s, i) => (
              <div key={s.label} className="flex items-center gap-3">
                <div className="flex flex-col items-center gap-2">
                  <div
                    className={`grid h-12 w-12 place-items-center rounded-2xl border ${
                      i === 3
                        ? "border-primary/60 bg-gradient-primary glow text-primary-foreground"
                        : "border-glass-border bg-glass text-cyan"
                    }`}
                  >
                    <s.icon className="h-5 w-5" />
                  </div>
                  <span className="font-mono text-[11px] text-muted-foreground">{s.label}</span>
                </div>
                {i < flowSteps.length - 1 && (
                  <ChevronRight className="h-5 w-5 shrink-0 text-muted-foreground/60" />
                )}
              </div>
            ))}
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-2">
            {[
              { t: "Stack analysis", d: "Frontend, backend, data layer detected from your repo." },
              { t: "Architecture", d: "Monolith, microservice, serverless, or hybrid." },
              { t: "Provider mix", d: "The right combo across compute, db, storage, edge." },
              { t: "Cost estimation", d: "Monthly cost ranges with risk warnings." },
              { t: "Deployment steps", d: "Copy-pasteable, ordered, beginner-friendly." },
              { t: "Config files", d: "Dockerfile, compose, GitHub Actions, Terraform." },
            ].map((c) => (
              <div
                key={c.t}
                className="flex items-start gap-3 rounded-2xl border border-glass-border bg-background/30 p-4"
              >
                <Check className="mt-0.5 h-4 w-4 shrink-0 text-mint" />
                <div>
                  <p className="font-medium">{c.t}</p>
                  <p className="text-sm text-muted-foreground">{c.d}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

/* ------------------------------- How It Works ------------------------------ */

const howSteps = [
  {
    n: "01",
    icon: Github,
    t: "Add Repository",
    d: "Paste your GitHub repository or upload your project.",
  },
  {
    n: "02",
    icon: Sparkles,
    t: "Select Service Type",
    d: "Frontend, backend, fullstack, AI model, or db-backed.",
  },
  {
    n: "03",
    icon: Globe,
    t: "Choose Target Location",
    d: "Where your users live — we recommend the region.",
  },
  {
    n: "04",
    icon: MessageSquare,
    t: "Chat with AI",
    d: "Describe budget, traffic, goal, and constraints.",
  },
  {
    n: "05",
    icon: Rocket,
    t: "Get Recommendation",
    d: "Architecture, provider, cost, region, and steps.",
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="relative py-24">
      <SectionHeader tag="How it works" title="Five steps to your deployment plan." />
      <div className="mx-auto mt-14 grid max-w-7xl gap-4 px-4 md:grid-cols-5">
        {howSteps.map((s) => (
          <div key={s.n} className="glass relative rounded-2xl p-5">
            <div className="flex items-center justify-between">
              <span className="font-mono text-xs text-muted-foreground">{s.n}</span>
              <s.icon className="h-4 w-4 text-cyan" />
            </div>
            <p className="mt-6 font-semibold">{s.t}</p>
            <p className="mt-1 text-sm text-muted-foreground">{s.d}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ----------------------------- Product Dashboard --------------------------- */

const sidebar = [
  { i: Sparkles, l: "New Analysis", active: true },
  { i: Boxes, l: "Projects" },
  { i: MessageSquare, l: "AI Chat" },
  { i: LayoutDashboard, l: "Architecture Advisor" },
  { i: Cloud, l: "Provider Comparison" },
  { i: DollarSign, l: "Cost Estimator" },
  { i: TerminalSquare, l: "Deployment Guide" },
  { i: Settings, l: "Settings" },
];

export function ProductDashboard() {
  const navigate = useNavigate();
  return (
    <section id="product" className="relative py-24">
      <SectionHeader
        tag="Product"
        title={
          <>
            The chatbot <span className="text-gradient">is the product.</span>
          </>
        }
        sub="A focused workspace: minimal setup on the left, AI chat on the right, structured results inline."
      />

      <div className="mx-auto mt-12 max-w-7xl px-4">
        <div className="glass ring-gradient overflow-hidden rounded-3xl shadow-card">
          {/* window chrome */}
          <div className="flex items-center justify-between border-b border-glass-border bg-background/40 px-4 py-3">
            <div className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded-full bg-destructive/70" />
              <span className="h-3 w-3 rounded-full bg-chart-4/70" />
              <span className="h-3 w-3 rounded-full bg-mint/70" />
            </div>
            <span className="font-mono text-xs text-muted-foreground">
              app.deploybuddy.dev / new-analysis
            </span>
            <span className="font-mono text-xs text-muted-foreground">⌘K</span>
          </div>

          <div className="grid grid-cols-12">
            {/* sidebar */}
            <aside className="col-span-12 border-b border-glass-border p-3 md:col-span-3 md:border-b-0 md:border-r md:p-4">
              <div className="mb-3 flex items-center gap-2 px-2">
                <span className="grid h-7 w-7 place-items-center rounded-md bg-gradient-primary">
                  <Rocket className="h-3.5 w-3.5 text-primary-foreground" />
                </span>
                <span className="text-sm font-semibold">DeployBuddy</span>
              </div>
              <nav className="space-y-1">
                {sidebar.map((s) => (
                  <button
                    key={s.l}
                    className={`flex w-full items-center gap-2.5 rounded-xl px-2.5 py-2 text-sm transition ${
                      s.active
                        ? "bg-primary/10 text-foreground ring-1 ring-primary/30"
                        : "text-muted-foreground hover:bg-glass hover:text-foreground"
                    }`}
                  >
                    <s.i className="h-4 w-4" />
                    {s.l}
                  </button>
                ))}
              </nav>
            </aside>

            {/* main */}
            <div className="col-span-12 grid gap-4 p-4 md:col-span-9 md:grid-cols-2 md:p-6">
              {/* setup form */}
              <div className="rounded-2xl border border-glass-border bg-background/30 p-5">
                <p className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
                  Quick Setup
                </p>
                <h3 className="mt-1 text-lg font-semibold">New Deployment Analysis</h3>

                <div className="mt-4 space-y-3">
                  {[
                    { l: "Repository URL", v: "github.com/acme/portal", icon: Github },
                    { l: "Service Type", v: "Fullstack App", icon: Sparkles },
                    { l: "Target Location", v: "Singapore", icon: Globe },
                  ].map((f) => (
                    <div
                      key={f.l}
                      className="rounded-xl border border-glass-border bg-glass px-3 py-2.5"
                    >
                      <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
                        {f.l}
                      </p>
                      <div className="mt-1 flex items-center gap-2 text-sm">
                        <f.icon className="h-3.5 w-3.5 text-cyan" />
                        <span className="font-mono">{f.v}</span>
                      </div>
                    </div>
                  ))}
                  <button
                    onClick={() => navigate({ to: "/chatbot" })}
                    className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-primary px-4 py-2.5 text-sm font-medium text-primary-foreground glow"
                  >
                    Continue with AI Chat <ArrowRight className="h-4 w-4" />
                  </button>
                </div>

                <div className="mt-5 rounded-xl border border-glass-border bg-glass p-3">
                  <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                    Detected stack
                  </p>
                  <div className="mt-2 flex flex-wrap gap-1.5 text-[11px]">
                    {["Next.js", "Golang", "PostgreSQL", "Tailwind", "Prisma"].map((s) => (
                      <span
                        key={s}
                        className="rounded-md border border-glass-border bg-background/50 px-2 py-0.5 font-mono text-cyan"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* chatbot */}
              <div className="rounded-2xl border border-primary/30 bg-background/30 p-5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="grid h-7 w-7 place-items-center rounded-md bg-gradient-accent">
                      <Bot className="h-3.5 w-3.5 text-primary-foreground" />
                    </div>
                    <p className="text-sm font-semibold">DeployBuddy AI</p>
                  </div>
                  <span className="font-mono text-[10px] text-mint">● online</span>
                </div>

                <div className="mt-4 space-y-3 text-sm">
                  <div className="flex gap-2">
                    <Avatar />
                    <div className="rounded-xl rounded-tl-sm border border-glass-border bg-secondary/60 p-3">
                      Deploy Next.js + Golang for SEA, $30/mo budget. MVP, scalable later.
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <BotAvatar />
                    <div className="space-y-2 rounded-xl rounded-tl-sm border border-primary/30 bg-primary/5 p-3">
                      <p>
                        Recommended: <span className="text-cyan">Vercel</span> +{" "}
                        <span className="text-violet">Railway</span> +{" "}
                        <span className="text-mint">Supabase</span> · Singapore.
                      </p>
                      <p className="font-mono text-[11px] text-muted-foreground">
                        est. $24–32/mo · 2 vCPU · 2 GB RAM
                      </p>
                    </div>
                  </div>
                </div>

                <div className="mt-4 flex items-center gap-2 rounded-xl border border-glass-border bg-background/40 p-2">
                  <input
                    placeholder="Describe your deployment goal, budget, traffic, provider preference..."
                    className="w-full bg-transparent px-2 text-xs outline-none placeholder:text-muted-foreground"
                  />
                  <button className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-primary glow">
                    <Send className="h-3.5 w-3.5 text-primary-foreground" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function Avatar() {
  return (
    <div className="grid h-7 w-7 shrink-0 place-items-center rounded-md bg-secondary text-muted-foreground">
      <User className="h-3.5 w-3.5" />
    </div>
  );
}
function BotAvatar() {
  return (
    <div className="grid h-7 w-7 shrink-0 place-items-center rounded-md bg-gradient-primary glow">
      <Bot className="h-3.5 w-3.5 text-primary-foreground" />
    </div>
  );
}

/* ------------------------------- Features --------------------------------- */

const features = [
  {
    i: GitBranch,
    t: "Repository Stack Detector",
    d: "Automatically identify languages, frameworks, and data layers.",
  },
  {
    i: MessageSquare,
    t: "Chat-Based Requirement Collector",
    d: "Capture budget, traffic, region and constraints in plain English.",
  },
  {
    i: LayoutDashboard,
    t: "Architecture Recommender",
    d: "Monolith, microservice, serverless, edge, or hybrid.",
  },
  {
    i: Cloud,
    t: "Provider Comparison Matrix",
    d: "Side-by-side compute, db, storage and edge options.",
  },
  {
    i: DollarSign,
    t: "FinOps Cost Estimator",
    d: "Monthly ranges, scaling thresholds, risk warnings.",
  },
  {
    i: FileCode2,
    t: "Infrastructure-as-Code Generator",
    d: "Dockerfile, docker-compose, GitHub Actions, Terraform.",
  },
  {
    i: TerminalSquare,
    t: "Interactive Deployment Guide",
    d: "Ordered, copy-pasteable steps tailored to your stack.",
  },
  {
    i: ShieldCheck,
    t: "Secrets & Env Var Guidance",
    d: "Where to put what, and how to keep it safe.",
  },
  { i: Zap, t: "Deployment Readiness Checker", d: "Health-checks before you push to production." },
];

export function Features() {
  return (
    <section id="features" className="relative py-24">
      <SectionHeader
        tag="Features"
        title={
          <>
            Everything you need to <span className="text-gradient">ship with confidence.</span>
          </>
        }
      />
      <div className="mx-auto mt-12 grid max-w-7xl gap-4 px-4 sm:grid-cols-2 lg:grid-cols-3">
        {features.map((f) => (
          <div
            key={f.t}
            className="glass group relative overflow-hidden rounded-2xl p-6 transition hover:-translate-y-0.5 hover:border-primary/40"
          >
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-primary text-primary-foreground glow">
              <f.i className="h-5 w-5" />
            </div>
            <h3 className="mt-5 font-semibold">{f.t}</h3>
            <p className="mt-1.5 text-sm text-muted-foreground">{f.d}</p>
            <span className="pointer-events-none absolute -right-10 -top-10 h-32 w-32 rounded-full bg-primary/10 opacity-0 blur-2xl transition group-hover:opacity-100" />
          </div>
        ))}
      </div>
    </section>
  );
}

/* --------------------------- AI Agent Workflow ---------------------------- */

const workflow = [
  { i: Github, t: "Repository URL" },
  { i: PackageSearch, t: "Stack Detector" },
  { i: MessageSquare, t: "User Prompt (Chatbot)" },
  { i: Sparkles, t: "Requirement Parser" },
  { i: Cloud, t: "Provider Knowledge Base" },
  { i: DollarSign, t: "Cost Estimator" },
  { i: LayoutDashboard, t: "Architecture Recommender" },
  { i: FileCode2, t: "Deployment Plan Generator" },
  { i: Bot, t: "Chatbot Result" },
];

export function AgentWorkflow() {
  return (
    <section className="relative py-24">
      <SectionHeader
        tag="AI workflow"
        title={
          <>
            Inside the <span className="text-gradient-accent">DeployBuddy agent.</span>
          </>
        }
        sub="A transparent pipeline — every step accountable, every recommendation explainable."
      />
      <div className="mx-auto mt-12 grid max-w-7xl gap-3 px-4 sm:grid-cols-2 md:grid-cols-3">
        {workflow.map((w, i) => (
          <div key={w.t} className="glass flex items-center gap-3 rounded-2xl p-4">
            <span className="font-mono text-[10px] text-muted-foreground">
              {String(i + 1).padStart(2, "0")}
            </span>
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-secondary text-cyan">
              <w.i className="h-4 w-4" />
            </div>
            <p className="text-sm font-medium">{w.t}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ------------------------- Example Chat Result ---------------------------- */

export function ChatExample() {
  return (
    <section className="relative py-24">
      <SectionHeader tag="Example output" title="A real recommendation, not a generic checklist." />

      <div className="mx-auto mt-12 grid max-w-6xl gap-5 px-4 lg:grid-cols-[1fr_1.4fr]">
        {/* user prompt */}
        <div className="glass rounded-3xl p-6">
          <div className="flex items-center gap-2 text-sm">
            <Avatar />
            <p className="font-semibold">You</p>
          </div>
          <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
            “Deploy my <span className="text-foreground">Next.js + Golang</span> app for users in
            Southeast Asia. Budget is <span className="text-foreground">$30/month</span>. I need a
            simple setup for MVP but still scalable later.”
          </p>
          <div className="mt-6 grid grid-cols-3 gap-2 text-center">
            {[
              { l: "Region", v: "SEA" },
              { l: "Budget", v: "$30/mo" },
              { l: "Stage", v: "MVP" },
            ].map((x) => (
              <div key={x.l} className="rounded-xl border border-glass-border bg-glass p-2">
                <p className="text-[10px] uppercase tracking-wider text-muted-foreground">{x.l}</p>
                <p className="mt-0.5 font-mono text-xs text-cyan">{x.v}</p>
              </div>
            ))}
          </div>
        </div>

        {/* AI response */}
        <div className="glass ring-gradient relative rounded-3xl p-6">
          <div className="flex items-center gap-2">
            <BotAvatar />
            <div>
              <p className="text-sm font-semibold">DeployBuddy AI</p>
              <p className="font-mono text-[10px] text-muted-foreground">
                recommendation #re-2026-0421
              </p>
            </div>
          </div>

          <div className="mt-5 space-y-4 text-sm">
            <Block title="Detected Stack">
              <Row k="Frontend" v="Next.js" />
              <Row k="Backend" v="Golang" />
              <Row k="Database" v="PostgreSQL" />
            </Block>

            <Block title="Recommended Architecture">
              <p>Simple microservice — separate web, api and managed db.</p>
            </Block>

            <Block title="Provider Recommendation">
              <Row k="Frontend" v="Vercel" />
              <Row k="Backend" v="Railway or DigitalOcean App Platform" />
              <Row k="Database" v="Supabase or Neon" />
            </Block>

            <div className="grid grid-cols-2 gap-3">
              <MiniBlock title="Region" value="Singapore" />
              <MiniBlock title="Resource" value="2 vCPU · 2 GB RAM" />
            </div>

            <div className="rounded-xl border border-destructive/40 bg-destructive/5 p-3">
              <div className="flex items-center gap-2 text-destructive">
                <AlertTriangle className="h-4 w-4" />
                <p className="text-sm font-medium">Cost warning</p>
              </div>
              <p className="mt-1 text-sm text-muted-foreground">
                $30/month suits MVP traffic. Plan to upgrade compute and db tier for stable high
                concurrency.
              </p>
            </div>

            <Block title="Deployment Steps">
              <ol className="ml-4 list-decimal space-y-1 text-sm text-muted-foreground marker:text-cyan">
                <li>Connect GitHub repository</li>
                <li>Deploy frontend to Vercel</li>
                <li>Deploy backend to Railway or DigitalOcean</li>
                <li>Create PostgreSQL database on Supabase or Neon</li>
                <li>Configure environment variables</li>
                <li>Set CORS and API base URL</li>
                <li>Test production endpoint</li>
                <li>Monitor usage and scale when traffic grows</li>
              </ol>
            </Block>

            <div className="rounded-xl border border-glass-border bg-background/50 p-3 font-mono text-[11px] leading-relaxed">
              <p className="text-muted-foreground"># generated/Dockerfile</p>
              <p>
                <span className="text-violet">FROM</span> golang:1.23-alpine{" "}
                <span className="text-cyan">AS</span> build
              </p>
              <p>
                <span className="text-violet">WORKDIR</span> /app
              </p>
              <p>
                <span className="text-violet">COPY</span> . .
              </p>
              <p>
                <span className="text-violet">RUN</span> go build -o server ./cmd/api
              </p>
              <p>
                <span className="text-violet">EXPOSE</span> 8080
              </p>
              <p>
                <span className="text-violet">CMD</span> [
                <span className="text-mint">"./server"</span>]
                <span className="animate-blink">▍</span>
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function Block({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-glass-border bg-glass p-3">
      <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
        {title}
      </p>
      <div className="mt-1.5 space-y-1">{children}</div>
    </div>
  );
}
function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-muted-foreground">{k}</span>
      <span className="font-mono text-foreground">{v}</span>
    </div>
  );
}
function MiniBlock({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-xl border border-glass-border bg-glass p-3">
      <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
        {title}
      </p>
      <p className="mt-1 text-sm font-medium">{value}</p>
    </div>
  );
}

/* ----------------------------- Providers --------------------------------- */

const providers = [
  { n: "AWS", c: "compute" },
  { n: "Azure", c: "compute" },
  { n: "GCP", c: "compute" },
  { n: "DigitalOcean", c: "compute" },
  { n: "Vercel", c: "edge" },
  { n: "Netlify", c: "edge" },
  { n: "Railway", c: "compute" },
  { n: "Supabase", c: "data" },
  { n: "Neon", c: "data" },
  { n: "Firebase", c: "data" },
  { n: "MongoDB Atlas", c: "data" },
  { n: "Hugging Face", c: "ai" },
  { n: "Replicate", c: "ai" },
  { n: "Modal", c: "ai" },
];

export function Providers() {
  return (
    <section id="providers" className="relative py-24">
      <SectionHeader
        tag="Provider ecosystem"
        title={
          <>
            14+ providers, <span className="text-gradient">one recommendation engine.</span>
          </>
        }
      />
      <div className="mx-auto mt-12 grid max-w-7xl grid-cols-2 gap-3 px-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7">
        {providers.map((p) => (
          <div
            key={p.n}
            className="glass group flex flex-col items-center justify-center gap-2 rounded-2xl p-5 transition hover:border-primary/40"
          >
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-secondary">
              {p.c === "compute" && <Server className="h-5 w-5 text-cyan" />}
              {p.c === "edge" && <Cloud className="h-5 w-5 text-violet" />}
              {p.c === "data" && <Database className="h-5 w-5 text-mint" />}
              {p.c === "ai" && <Sparkles className="h-5 w-5 text-primary" />}
            </div>
            <span className="text-xs font-medium">{p.n}</span>
            <span className="font-mono text-[9px] uppercase tracking-wider text-muted-foreground">
              {p.c}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}

/* --------------------------- System Architecture -------------------------- */

const arch = [
  ["User", "Web App", "Quick Setup Form"],
  ["AI Chatbot", "Backend API", "AI Agent Service"],
  ["Repository Analyzer", "Provider Knowledge Base", "Cost Estimator"],
  ["Recommendation Engine", "Deployment Result", ""],
];

export function Architecture() {
  return (
    <section className="relative py-24">
      <SectionHeader
        tag="System architecture"
        title="A pipeline you can trust."
        sub="Each layer is independently observable, swappable, and auditable."
      />
      <div className="mx-auto mt-12 max-w-6xl px-4">
        <div className="glass ring-gradient rounded-3xl p-6 md:p-10">
          <div className="space-y-4">
            {arch.map((row, i) => (
              <div key={i} className="grid gap-3 md:grid-cols-3">
                {row.map((node) =>
                  node ? (
                    <div
                      key={node}
                      className="rounded-2xl border border-glass-border bg-background/40 px-4 py-3 text-center font-mono text-sm"
                    >
                      <span className="text-cyan">{node}</span>
                    </div>
                  ) : (
                    <div key={Math.random()} />
                  ),
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

/* -------------------------------- Pricing -------------------------------- */

// const tiers = [
//   {
//     name: "Free", price: "$0", sub: "Try DeployBuddy",
//     features: ["3 AI recommendations/month", "Basic repository analysis", "Basic provider recommendation", "Manual deployment guide"],
//     cta: "Start free", featured: false,
//   },
//   {
//     name: "Pro", price: "$19", sub: "per month",
//     features: ["Unlimited recommendations", "Advanced AI chatbot", "Cost estimation", "Provider comparison", "IaC config suggestions", "Deployment guide export"],
//     cta: "Upgrade to Pro", featured: true,
//   },
//   {
//     name: "Team", price: "$49", sub: "per seat / month",
//     features: ["Shared projects", "Team collaboration", "Deployment history", "Provider credential management", "Advanced workspace"],
//     cta: "Start team trial", featured: false,
//   },
// ];

// export function Pricing() {
//   return (
//     <section id="pricing" className="relative py-24">
//       <SectionHeader tag="Pricing" title="Start free. Upgrade when you ship." />
//       <div className="mx-auto mt-12 grid max-w-6xl gap-5 px-4 md:grid-cols-3">
//         {tiers.map((t) => (
//           <div
//             key={t.name}
//             className={`relative rounded-3xl p-6 ${t.featured
//                 ? "ring-gradient bg-gradient-to-b from-primary/10 to-transparent shadow-card glow"
//                 : "glass"
//               }`}
//           >
//             {t.featured && (
//               <span className="absolute -top-3 left-6 rounded-full bg-gradient-primary px-3 py-1 font-mono text-[10px] uppercase tracking-wider text-primary-foreground">
//                 Most popular
//               </span>
//             )}
//             <p className="text-sm font-medium text-muted-foreground">{t.name}</p>
//             <div className="mt-3 flex items-baseline gap-1">
//               <span className="text-4xl font-semibold tracking-tight">{t.price}</span>
//               <span className="text-sm text-muted-foreground">{t.sub}</span>
//             </div>
//             <ul className="mt-6 space-y-2.5">
//               {t.features.map((f) => (
//                 <li key={f} className="flex items-start gap-2 text-sm">
//                   <Check className="mt-0.5 h-4 w-4 shrink-0 text-mint" />
//                   <span>{f}</span>
//                 </li>
//               ))}
//             </ul>
//             <button
//               className={`mt-6 w-full rounded-xl px-4 py-2.5 text-sm font-medium transition ${t.featured
//                   ? "bg-gradient-primary text-primary-foreground glow hover:opacity-90"
//                   : "border border-glass-border bg-glass hover:border-primary/40"
//                 }`}
//             >
//               {t.cta}
//             </button>
//           </div>
//         ))}
//       </div>
//     </section>
//   );
// }

/* --------------------------------- Keys ---------------------------------- */

const PROVIDER_KEYS: {
  provider: string;
  fields: { key: string; label: string; placeholder: string }[];
}[] = [
  {
    provider: "AWS",
    fields: [
      { key: "aws_access_key_id", label: "Access Key ID", placeholder: "AKIAIOSFODNN7EXAMPLE" },
      {
        key: "aws_secret_access_key",
        label: "Secret Access Key",
        placeholder: "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
      },
    ],
  },
  {
    provider: "Vercel",
    fields: [{ key: "vercel_token", label: "API Token", placeholder: "vercel_xxxxxxxxxxxxxxxx" }],
  },
  {
    provider: "Railway",
    fields: [{ key: "railway_token", label: "API Token", placeholder: "railway_xxxxxxxxxxxxxxxx" }],
  },
  {
    provider: "Supabase",
    fields: [
      { key: "supabase_url", label: "Project URL", placeholder: "https://xxxx.supabase.co" },
      { key: "supabase_anon_key", label: "Anon Key", placeholder: "eyJhbGciOiJIUzI1NiIs..." },
      {
        key: "supabase_service_key",
        label: "Service Role Key",
        placeholder: "eyJhbGciOiJIUzI1NiIs...",
      },
    ],
  },
  {
    provider: "DigitalOcean",
    fields: [
      { key: "do_token", label: "Personal Access Token", placeholder: "dop_v1_xxxxxxxxxxxxxxxx" },
    ],
  },
  {
    provider: "GCP",
    fields: [
      { key: "gcp_project_id", label: "Project ID", placeholder: "my-project-123456" },
      {
        key: "gcp_service_account_json",
        label: "Service Account JSON",
        placeholder: '{ "type": "service_account", ... }',
      },
    ],
  },
  {
    provider: "Azure",
    fields: [
      {
        key: "azure_subscription_id",
        label: "Subscription ID",
        placeholder: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
      },
      {
        key: "azure_client_id",
        label: "Client ID",
        placeholder: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
      },
      {
        key: "azure_client_secret",
        label: "Client Secret",
        placeholder: "xxxxxxxxxxxxxxxxxxxxxxxx",
      },
    ],
  },
  {
    provider: "Netlify",
    fields: [
      { key: "netlify_token", label: "Personal Access Token", placeholder: "nfp_xxxxxxxxxxxxxxxx" },
    ],
  },
  {
    provider: "Render",
    fields: [{ key: "render_api_key", label: "API Key", placeholder: "rnd_xxxxxxxxxxxxxxxx" }],
  },
  {
    provider: "Fly.io",
    fields: [{ key: "fly_api_token", label: "API Token", placeholder: "FlyV1 xxxxxxxxxxxxxxxx" }],
  },
];

export function Keys() {
  const [selected, setSelected] = useState<string>(PROVIDER_KEYS[0].provider);
  const [values, setValues] = useState<Record<string, string>>({});
  const [visible, setVisible] = useState<Record<string, boolean>>({});
  const [saved, setSaved] = useState<Record<string, boolean>>({});

  const activeProvider = PROVIDER_KEYS.find((p) => p.provider === selected)!;

  function toggleVisible(key: string) {
    setVisible((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  function handleSave() {
    setSaved((prev) => ({ ...prev, [selected]: true }));
    setTimeout(() => setSaved((prev) => ({ ...prev, [selected]: false })), 2000);
  }

  function handleClear() {
    activeProvider.fields.forEach((f) => {
      setValues((prev) => ({ ...prev, [f.key]: "" }));
    });
    setSaved((prev) => ({ ...prev, [selected]: false }));
  }

  const isProviderFilled = (provider: (typeof PROVIDER_KEYS)[number]) =>
    provider.fields.every((f) => !!values[f.key]);

  return (
    <section id="keys" className="relative py-24">
      <SectionHeader
        tag="Provider Keys"
        title={
          <>
            Manage your <span className="text-gradient">API credentials.</span>
          </>
        }
        sub="Store your provider API keys securely. Keys are only used during AI analysis and never shared."
      />

      <div className="mx-auto mt-12 max-w-6xl px-4">
        <div className="glass ring-gradient overflow-hidden rounded-3xl shadow-card">
          {/* window chrome */}
          <div className="flex items-center justify-between border-b border-glass-border bg-background/40 px-4 py-3">
            <div className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded-full bg-destructive/70" />
              <span className="h-3 w-3 rounded-full bg-chart-4/70" />
              <span className="h-3 w-3 rounded-full bg-mint/70" />
            </div>
            <span className="font-mono text-xs text-muted-foreground">
              app.deploybuddy.dev / keys
            </span>
            <span className="font-mono text-xs text-muted-foreground">🔒 local only</span>
          </div>

          <div className="grid md:grid-cols-[240px_1fr]">
            {/* ── Left panel: provider list ── */}
            <aside className="border-b border-glass-border md:border-b-0 md:border-r md:border-glass-border">
              <div className="p-3">
                <p className="px-2 pb-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                  Providers
                </p>
                <nav className="space-y-1">
                  {PROVIDER_KEYS.map((p) => {
                    const filled = isProviderFilled(p);
                    return (
                      <button
                        key={p.provider}
                        onClick={() => setSelected(p.provider)}
                        className={`flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-sm transition ${
                          selected === p.provider
                            ? "bg-primary/10 text-foreground ring-1 ring-primary/30"
                            : "text-muted-foreground hover:bg-glass hover:text-foreground"
                        }`}
                      >
                        <div className="flex items-center gap-2.5">
                          <div
                            className={`grid h-7 w-7 place-items-center rounded-lg ${
                              selected === p.provider ? "bg-gradient-primary glow" : "bg-secondary"
                            }`}
                          >
                            <Key className="h-3.5 w-3.5 text-primary-foreground" />
                          </div>
                          <span className="font-medium">{p.provider}</span>
                        </div>
                        {filled && (
                          <span className="h-2 w-2 rounded-full bg-mint" title="Key saved" />
                        )}
                      </button>
                    );
                  })}
                </nav>
              </div>
            </aside>

            {/* ── Right panel: form ── */}
            <div className="p-5 md:p-6">
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <h3 className="font-semibold">{activeProvider.provider}</h3>
                  <p className="mt-0.5 font-mono text-[11px] text-muted-foreground">
                    {activeProvider.fields.length} credential
                    {activeProvider.fields.length > 1 ? "s" : ""} required
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleClear}
                    className="flex items-center gap-1.5 rounded-xl border border-glass-border bg-glass px-3 py-1.5 text-xs text-muted-foreground transition hover:border-destructive/40 hover:text-destructive"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    Clear
                  </button>
                  <button
                    onClick={handleSave}
                    className="flex items-center gap-1.5 rounded-xl bg-gradient-primary px-3 py-1.5 text-xs font-medium text-primary-foreground glow transition hover:opacity-90"
                  >
                    <Plus className="h-3.5 w-3.5" />
                    {saved[selected] ? "Saved ✓" : "Save Keys"}
                  </button>
                </div>
              </div>

              <div className="space-y-3">
                {activeProvider.fields.map((field) => (
                  <div
                    key={field.key}
                    className="rounded-xl border border-glass-border bg-background/30"
                  >
                    <div className="flex items-center justify-between border-b border-glass-border px-3 py-2">
                      <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                        {field.label}
                      </p>
                      <button
                        onClick={() => toggleVisible(field.key)}
                        className="text-muted-foreground transition hover:text-foreground"
                      >
                        {visible[field.key] ? (
                          <EyeOff className="h-3.5 w-3.5" />
                        ) : (
                          <Eye className="h-3.5 w-3.5" />
                        )}
                      </button>
                    </div>
                    <input
                      type={visible[field.key] ? "text" : "password"}
                      value={values[field.key] ?? ""}
                      onChange={(e) =>
                        setValues((prev) => ({ ...prev, [field.key]: e.target.value }))
                      }
                      placeholder={field.placeholder}
                      className="w-full bg-transparent px-3 py-2.5 font-mono text-sm outline-none placeholder:text-muted-foreground/50"
                    />
                  </div>
                ))}
              </div>

              {/* info note */}
              <div className="mt-5 flex items-start gap-2 rounded-xl border border-glass-border bg-glass px-3 py-2.5 text-xs text-muted-foreground">
                <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-mint" />
                <p>
                  Keys are stored locally in your browser and never sent to our servers. They are
                  only used to interact directly with provider APIs during deployment analysis.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ----------------------------- Final CTA + Footer ------------------------- */

export function FinalCTA() {
  return (
    <section id="start" className="relative py-24">
      <div className="mx-auto max-w-5xl px-4">
        <div className="glass ring-gradient relative overflow-hidden rounded-3xl p-10 md:p-16 text-center">
          <span className="pointer-events-none absolute -top-20 left-1/2 h-64 w-[80%] -translate-x-1/2 rounded-full bg-primary/30 blur-3xl" />
          <SectionTag>Get started</SectionTag>
          <h2 className="mt-4 text-balance text-3xl font-semibold tracking-tight md:text-5xl">
            Ready to ask AI <span className="text-gradient">how to deploy your app?</span>
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-pretty text-muted-foreground">
            Paste your repository, select your service type and location, then chat with DeployBuddy
            AI to get your deployment plan.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <button className="flex items-center gap-2 rounded-2xl bg-gradient-primary px-5 py-3 text-sm font-medium text-primary-foreground glow hover:opacity-90 transition">
              Start with AI Chat <ArrowRight className="h-4 w-4" />
            </button>
            <button className="rounded-2xl border border-glass-border bg-glass px-5 py-3 text-sm font-medium hover:border-primary/40 transition">
              Read the docs
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}

export function Footer() {
  return (
    <footer className="border-t border-glass-border py-10">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 text-sm text-muted-foreground md:flex-row">
        <div className="flex items-center gap-2">
          <span className="grid h-6 w-6 place-items-center rounded-md bg-gradient-primary">
            <Rocket className="h-3 w-3 text-primary-foreground" />
          </span>
          <span className="font-semibold text-foreground">DeployBuddy</span>
          <span className="font-mono text-xs">© 2026</span>
        </div>
        <div className="flex items-center gap-5">
          <a href="#" className="hover:text-foreground">
            Privacy
          </a>
          <a href="#" className="hover:text-foreground">
            Terms
          </a>
          <a href="#" className="hover:text-foreground">
            Status
          </a>
          <a href="#" className="hover:text-foreground">
            Contact
          </a>
        </div>
      </div>
    </footer>
  );
}
