import { Rocket } from "lucide-react";

// const links = ["Product", "Features", "How It Works", "Providers", "Pricing", "Keys"];

const links = ["Product", "Features", "How It Works", "Providers", "Keys"];

export function Navbar() {
  return (
    <header className="fixed top-4 inset-x-0 z-50 px-4">
      <nav className="glass mx-auto flex max-w-6xl items-center justify-between rounded-2xl px-4 py-2.5 shadow-card">
        <a href="#top" className="flex items-center gap-2">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-primary glow">
            <Rocket className="h-4 w-4 text-primary-foreground" />
          </span>
          <span className="font-semibold tracking-tight">DeployBuddy</span>
        </a>
        <ul className="hidden md:flex items-center gap-7 text-sm text-muted-foreground">
          {links.map((l) => (
            <li key={l}>
              <a
                href={`#${l.toLowerCase().replace(/\s/g, "-")}`}
                className="hover:text-foreground transition-colors"
              >
                {l}
              </a>
            </li>
          ))}
        </ul>
        <a
          href="#start"
          className="rounded-xl bg-gradient-primary px-4 py-2 text-sm font-medium text-primary-foreground glow hover:opacity-90 transition"
        >
          Get Started
        </a>
      </nav>
    </header>
  );
}
