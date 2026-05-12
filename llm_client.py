import os
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
        genai.configure(api_key=api_key)
        self.model = model

    def generate(self, prompt: str, max_tokens: int = 2048) -> str:
        model = genai.GenerativeModel(self.model)
        response = model.generate_content(prompt, generation_config={"max_output_tokens": max_tokens})
        return response.text

# ---------- Local / OpenAI-compatible (Ollama, vLLM) ----------
from openai import OpenAI

class LocalOpenAILLM(LLMClient):
    def __init__(self, base_url: str = "http://localhost:11434/v1", model: str = "llama3"):
        self.client = OpenAI(base_url=base_url, api_key="not-needed")
        self.model = model

    def generate(self, prompt: str, max_tokens: int = 2048) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content

# Factory untuk memilih LLM backend
def get_llm_client(backend: str, **kwargs) -> LLMClient:
    if backend == "groq":
        return GroqLLM(**kwargs)
    elif backend == "google":
        return GoogleLLM(**kwargs)
    elif backend == "local":
        return LocalOpenAILLM(**kwargs)
    else:
        raise ValueError(f"Unsupported backend: {backend}")