import os
import json
from abc import ABC, abstractmethod

class LLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 2048) -> str:
        pass

# ---------- Groq ----------
try:
    from groq import Groq
except ImportError:
    Groq = None

class GroqLLM(LLMClient):
    def __init__(self, api_key: str, model: str = "llama3-8b-8192"):
        if Groq is None:
            raise ImportError("Package 'groq' belum terinstall. Jalankan: pip install groq")
        self.client = Groq(api_key=api_key)
        self.model = model

    def generate(self, prompt: str, max_tokens: int = 2048) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content

# ---------- Google AI Studio ----------
try:
    import google.generativeai as genai
except ImportError:
    genai = None

class GoogleLLM(LLMClient):
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        if genai is None:
            raise ImportError("Package 'google-generativeai' belum terinstall. Jalankan: pip install google-generativeai")
        genai.configure(api_key=api_key)
        self.model = model

    def generate(self, prompt: str, max_tokens: int = 2048) -> str:
        model = genai.GenerativeModel(self.model)
        response = model.generate_content(prompt, generation_config={"max_output_tokens": max_tokens})
        return response.text

# ---------- Local / OpenAI-compatible (Ollama, vLLM) ----------
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

class LocalOpenAILLM(LLMClient):
    def __init__(self, base_url: str = "http://localhost:11434/v1", model: str = "llama3", api_key: str = "not-needed"):
        if OpenAI is None:
            raise ImportError("Package 'openai' belum terinstall. Jalankan: pip install openai")
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = model

    def generate(self, prompt: str, max_tokens: int = 2048) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content


class MockLLM(LLMClient):
    """Deterministic offline LLM for tests and demos without API keys."""

    def generate(self, prompt: str, max_tokens: int = 2048) -> str:
        lower = prompt.lower()
        if "deployment package in markdown" in lower:
            return """## FILE: Dockerfile

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD [\"python\", \"main.py\"]
```

## FILE: .env.example

```env
LLM_BACKEND=groq
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

## GUIDE

Deploy the application to Modal.com or another Python-capable compute provider. Keep API keys in environment variables.

## VERIFY

```powershell
python main.py
```
"""

        is_ml_workload = "primary workload:\nml" in lower or "primary workload classification:\nml" in lower
        provider = "Modal.com" if is_ml_workload else "Railway"
        category = "ml_best" if provider == "Modal.com" else "backend"
        plan = {
            "architecture_diagram": "flowchart TD\n  User-->App\n  App-->VectorDB\n  App-->LLM",
            "provider": provider,
            "provider_category": category,
            "service_model": "Container",
            "region": "Singapore",
            "resource_spec": {"cpu": "2 vCPU", "ram_gb": "4", "storage_gb": "20", "gpu": "none"},
            "estimated_monthly_cost_usd": 30,
            "provider_comparison_matrix": [
                {
                    "provider": provider,
                    "category": category,
                    "estimated_monthly_cost_usd": 30,
                    "maintenance_effort": "medium",
                    "scalability": "medium",
                    "fit_reason": "Mock recommendation for offline validation.",
                    "tradeoff": "Replace with live LLM and current provider pricing before production use.",
                }
            ],
            "supporting_services": [],
            "guide": "1. Configure environment variables.\n2. Deploy as a container.\n3. Verify the health endpoint or CLI output.",
            "deployment_plan": {"provider": provider, "region": "Singapore", "runtime": "python"},
            "risk_notes": "Mock output for local testing only.",
            "confidence": "low",
        }
        return json.dumps(plan)

# Factory untuk memilih LLM backend
def get_llm_client(backend: str, **kwargs) -> LLMClient:
    if backend == "groq":
        return GroqLLM(**kwargs)
    elif backend == "google":
        return GoogleLLM(**kwargs)
    elif backend == "local":
        return LocalOpenAILLM(**kwargs)
    elif backend == "mock":
        return MockLLM()
    else:
        raise ValueError(f"Unsupported backend: {backend}")


def get_llm_client_from_env() -> tuple[str, LLMClient]:
    backend = os.getenv("LLM_BACKEND") or os.getenv("LLM_PROVIDER", "groq")
    backend = backend.strip().lower()
    if backend == "ollama":
        backend = "local"
    if backend == "groq":
        return backend, get_llm_client(
            "groq",
            api_key=os.getenv("GROQ_API_KEY"),
            model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        )
    if backend == "google":
        return backend, get_llm_client(
            "google",
            api_key=os.getenv("GOOGLE_API_KEY"),
            model=os.getenv("GOOGLE_MODEL", "gemini-1.5-flash"),
        )
    if backend == "local":
        base_url = os.getenv("LOCAL_BASE_URL") or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        if base_url and not base_url.rstrip("/").endswith("/v1"):
            base_url = base_url.rstrip("/") + "/v1"
        return backend, get_llm_client(
            "local",
            base_url=base_url,
            model=os.getenv("LOCAL_MODEL") or os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
            api_key=os.getenv("LOCAL_API_KEY", "not-needed"),
        )
    if backend == "openai":
        return backend, get_llm_client(
            "local",
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_key=os.getenv("OPENAI_API_KEY", ""),
        )
    if backend == "mock":
        return backend, get_llm_client("mock")
    raise ValueError(f"Backend LLM '{backend}' tidak dikenal.")
