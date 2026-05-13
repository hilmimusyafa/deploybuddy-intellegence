const API_BASE_URL = import.meta.env.VITE_DEPLOYBUDDY_API_URL ?? "http://localhost:8000";

function normalizeRepoUrl(repo: string): string {
  const trimmed = repo.trim();
  if (trimmed.startsWith("github.com/")) {
    return `https://${trimmed}`;
  }
  return trimmed;
}

function normalizeServiceType(service: string): string {
  const value = service
    .trim()
    .toLowerCase()
    .replace(/[-\s]+/g, "_");
  const aliases: Record<string, string> = {
    fullstack: "web_application",
    fullstack_app: "web_application",
    full_stack: "web_application",
    full_stack_app: "web_application",
    web: "web_application",
    web_app: "web_application",
    frontend_app: "frontend",
    static_site: "frontend",
    api: "backend",
    api_service: "backend",
    backend_api: "backend",
    backend_service: "backend",
    ai_model: "model",
    model_ai: "model",
  };
  return aliases[value] ?? value ?? "auto";
}

async function requestJson<T>(path: string, init: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...(init.headers ?? {}),
    },
  });

  if (!response.ok) {
    let detail = `Backend request failed with status ${response.status}`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      // Keep the generic message when the backend does not return JSON.
    }
    throw new Error(detail);
  }

  return (await response.json()) as T;
}

export async function generateDeploymentAnalysis(
  repo: string,
  service: string,
  region: string,
  budget: string,
  userRequest: string,
): Promise<string> {
  const result = await requestJson<{ ui_recommendation: unknown }>("/deploy", {
    method: "POST",
    body: JSON.stringify({
      repo_url: normalizeRepoUrl(repo),
      budget: Number.parseInt(budget, 10) || 30,
      ccu: 200,
      region,
      service_type: normalizeServiceType(service || "auto"),
      max_snippets: 2,
      user_message: userRequest,
    }),
  });

  return JSON.stringify(result.ui_recommendation);
}

export async function generateFollowUpResponse(
  userMessage: string,
  context: {
    repo: string;
    service: string;
    region: string;
    budget?: string;
    previousAnalysis?: Record<string, unknown>;
  },
): Promise<string> {
  const provider = String(context.previousAnalysis?.providers ?? "the recommended provider");
  const risk = String(
    context.previousAnalysis?.risk ?? "review the generated package before deploying",
  );

  await requestJson("/conversation", {
    method: "POST",
    body: JSON.stringify({
      title: `Follow-up for ${context.repo}`,
      messages: [
        {
          role: "user",
          content: userMessage,
          context: {
            repo: context.repo,
            service: context.service,
            region: context.region,
            budget: context.budget,
          },
        },
      ],
    }),
  });

  return `For ${provider}, keep the next step focused on validating environment variables, reviewing the generated deployment package, and running a dry-run deploy first. Main risk to watch: ${risk}`;
}
