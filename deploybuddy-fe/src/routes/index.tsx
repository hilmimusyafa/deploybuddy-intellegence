import { createFileRoute } from "@tanstack/react-router";
import { ArrowRight, PlayCircle, Sparkles } from "lucide-react";
import { Navbar } from "@/components/site/Navbar";
import { SetupAndChat } from "@/components/site/SetupAndChat";
// import {
//   Problem, ChatbotFirst, HowItWorks, ProductDashboard, Features,
//   AgentWorkflow, ChatExample, Providers, Architecture, Pricing, FinalCTA, Footer,
// } from "@/components/site/Sections";
import {
  Problem,
  ChatbotFirst,
  HowItWorks,
  ProductDashboard,
  Features,
  AgentWorkflow,
  ChatExample,
  Providers,
  Architecture,
  FinalCTA,
  Footer,
} from "@/components/site/Sections";
import { Keys } from "@/components/site/Sections";

export const Route = createFileRoute("/")({
  component: Index,
});

function Index() {
  return (
    <div id="top" className="relative min-h-screen overflow-hidden bg-hero">
      {/* Ambient blobs */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 left-1/3 h-[40rem] w-[40rem] rounded-full bg-primary/20 blur-[140px]" />
        <div className="absolute top-[40%] -right-40 h-[36rem] w-[36rem] rounded-full bg-violet/20 blur-[140px]" />
        <div className="absolute bottom-0 -left-40 h-[30rem] w-[30rem] rounded-full bg-cyan/15 blur-[140px]" />
      </div>

      <Navbar />

      {/* Hero */}
      <section className="relative px-4 pt-36 pb-20 md:pt-44">
        <div className="mx-auto max-w-7xl">
          <div className="text-center">
            <span className="inline-flex items-center gap-2 rounded-full border border-glass-border bg-glass px-3 py-1 font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
              <Sparkles className="h-3.5 w-3.5 text-cyan" />
              AI deployment advisor · v2026.1
            </span>
            <h1 className="mt-5 text-balance text-4xl font-semibold tracking-tight md:text-7xl">
              Deploy <span className="text-gradient">smarter</span>{" "}
              <br className="hidden md:block" />
              with <span className="text-gradient-accent">AI.</span>
            </h1>
            <p className="mx-auto mt-5 max-w-2xl text-pretty text-muted-foreground md:text-lg">
              Connect your repository, choose your service type and target region, then chat with
              DeployBuddy AI to get a practical deployment plan.
            </p>
            <div className="mt-7 flex flex-wrap items-center justify-center gap-3">
              <a
                href="#start"
                className="flex items-center gap-2 rounded-2xl bg-gradient-primary px-5 py-3 text-sm font-medium text-primary-foreground glow hover:opacity-90 transition"
              >
                Start Deployment Analysis <ArrowRight className="h-4 w-4" />
              </a>
              <a
                href="#product"
                className="flex items-center gap-2 rounded-2xl border border-glass-border bg-glass px-5 py-3 text-sm font-medium hover:border-primary/40 transition"
              >
                <PlayCircle className="h-4 w-4 text-cyan" /> View Demo
              </a>
            </div>
            <div className="mt-5 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 font-mono text-[11px] text-muted-foreground">
              <span>● No credit card required</span>
              <span>● 14+ providers</span>
              <span>● Step-by-step deploy guides</span>
            </div>
          </div>

          <div className="mx-auto mt-14 max-w-6xl">
            <SetupAndChat />
          </div>
        </div>
      </section>

      <Problem />
      <ChatbotFirst />
      <HowItWorks />
      <ProductDashboard />
      <Features />
      <AgentWorkflow />
      <ChatExample />
      <Providers />
      <Architecture />
      {/* <Pricing /> */}
      <Keys />
      <FinalCTA />
      <Footer />
    </div>
  );
}
