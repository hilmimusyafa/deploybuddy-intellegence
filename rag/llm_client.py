"""
DeployBuddy RAG — Dynamic LLM Client
======================================
Satu interface untuk Ollama (lokal), OpenAI, Anthropic, dan Groq.
Semua dikontrol dari config.py atau environment variable.
"""

import json
import requests
from config import LLM_PROVIDER, LLM_CONFIGS, MAX_TOKENS, TEMPERATURE


class LLMClient:
    """
    Universal LLM client. Penggunaan:
        client = LLMClient()
        response = client.chat(system_prompt, user_message)
    """

    def __init__(self, provider: str = None):
        self.provider = provider or LLM_PROVIDER
        self.cfg = LLM_CONFIGS[self.provider]
        print(f"[LLMClient] Using provider: {self.provider} | model: {self.cfg['model']}")

    def chat(self, system_prompt: str, user_message: str) -> str:
        """Kirim pesan ke LLM, return response string."""
        if self.provider == "ollama":
            return self._call_ollama(system_prompt, user_message)
        elif self.provider == "anthropic":
            return self._call_anthropic(system_prompt, user_message)
        else:
            # openai-compatible: openai, groq
            return self._call_openai_compat(system_prompt, user_message)

    # ──────────────────────────────────────────
    # Ollama (local)
    # ──────────────────────────────────────────
    def _call_ollama(self, system_prompt: str, user_message: str) -> str:
        url = f"{self.cfg['base_url']}/api/chat"
        payload = {
            "model": self.cfg["model"],
            "stream": False,
            "options": {
                "temperature": TEMPERATURE,
                "num_predict": MAX_TOKENS,
            },
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message},
            ],
        }
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data["message"]["content"]

    # ──────────────────────────────────────────
    # OpenAI-compatible (OpenAI, Groq)
    # ──────────────────────────────────────────
    def _call_openai_compat(self, system_prompt: str, user_message: str) -> str:
        url = f"{self.cfg['base_url']}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.cfg['api_key']}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.cfg["model"],
            "temperature": TEMPERATURE,
            "max_tokens": MAX_TOKENS,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message},
            ],
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    # ──────────────────────────────────────────
    # Anthropic (Claude)
    # ──────────────────────────────────────────
    def _call_anthropic(self, system_prompt: str, user_message: str) -> str:
        url = f"{self.cfg['base_url']}/messages"
        headers = {
            "x-api-key": self.cfg["api_key"],
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.cfg["model"],
            "max_tokens": MAX_TOKENS,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_message},
            ],
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data["content"][0]["text"]
