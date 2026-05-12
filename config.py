"""
DeployBuddy RAG — Configuration
================================
Semua pengaturan LLM dan RAG ada di sini.
Ganti LLM_PROVIDER sesuai kebutuhan (ollama / openai / anthropic / groq).
"""

import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _default_data_path(filename: str) -> str:
    return os.path.join(BASE_DIR, "data", filename)


def _resolve_data_path(env_name: str, filename: str) -> str:
    configured = os.getenv(env_name)
    if not configured:
        return _default_data_path(filename)
    configured = os.path.expanduser(configured)
    if os.path.isabs(configured):
        return configured
    rag_relative = os.path.join(BASE_DIR, configured)
    if os.path.exists(rag_relative):
        return rag_relative
    return configured

# ─────────────────────────────────────────────
# 🤖  LLM PROVIDER — pilih salah satu:
#   "ollama"    → lokal (Ollama)
#   "openai"    → OpenAI API
#   "anthropic" → Anthropic Claude API
#   "groq"      → Groq (free tier, cepat)
# ─────────────────────────────────────────────
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")

LLM_CONFIGS = {
    "ollama": {
        "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "model":    os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
        "api_key":  None,
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "model":    os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "api_key":  os.getenv("OPENAI_API_KEY", ""),
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com/v1",
        "model":    os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
        "api_key":  os.getenv("ANTHROPIC_API_KEY", ""),
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "model":    os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "api_key":  os.getenv("GROQ_API_KEY", ""),
    },
    "mock": {
        "base_url": "",
        "model":    "deploybuddy-mock",
        "api_key":  None,
    },
}

# ─────────────────────────────────────────────
# 📁  Dataset CSV paths (detachable — ganti sesuai lokasi file)
# ─────────────────────────────────────────────
PRICING_CSV_PATH    = _resolve_data_path("PRICING_CSV_PATH", "provider_pricing_curated.csv")
DEPLOY_API_CSV_PATH = _resolve_data_path("DEPLOY_API_CSV_PATH", "provider_deploy_api.csv")

# ─────────────────────────────────────────────
# 🔍  RAG Settings
# ─────────────────────────────────────────────
RAG1_TOP_K = int(os.getenv("RAG1_TOP_K", "12"))   # berapa banyak baris pricing yang di-retrieve
RAG2_TOP_K = int(os.getenv("RAG2_TOP_K", "3"))    # berapa provider deploy API yang di-retrieve

# ─────────────────────────────────────────────
# 🌡️  LLM Generation params
# ─────────────────────────────────────────────
MAX_TOKENS   = int(os.getenv("MAX_TOKENS", "4096"))
TEMPERATURE  = float(os.getenv("TEMPERATURE", "0.3"))
