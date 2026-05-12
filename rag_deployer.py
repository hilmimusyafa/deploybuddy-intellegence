"""
DeployBuddy — RAG System 2: Deploy Code Generator
==================================================
ALUR:
  Hasil JSON dari RAG System 1 (deploy_json)
       ↓
  [RETRIEVAL] Lookup provider di provider_deploy_api.csv
              (exact match + TF-IDF fallback untuk provider serupa)
       ↓
  [INJECT] Deploy API docs tiap provider → context block
       ↓
  [LLM INFERENCE] Generate kode Python (API/SDK calls) + env var template
       ↓
  Output:
    - deploy.py   : script Python siap pakai untuk auto-deploy
    - .env.example: template environment variables / secrets
    - README.md   : langkah-langkah manual deployment

INPUT: ArchitectureResult.deploy_json (dari RAG System 1)

Contoh deploy_json:
{
  "recommended_architecture": "container",
  "providers": [
    {"provider": "AWS", "product": "ECS on Fargate", "region": "ap-southeast-1",
     "plan": "0.25vCPU-0.5GB", "service_type": "container", "role": "backend"},
    {"provider": "Supabase", "product": "Supabase Postgres", "role": "database"}
  ],
  "deployment_steps_summary": ["step 1", ...],
  "risks": ["risk 1", ...]
}
"""

import re
from typing import List, Dict, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import DEPLOY_API_CSV_PATH, RAG2_TOP_K
from data_loader import load_deploy_api_chunks, deploy_api_chunk_to_context
from llm_client import LLMClient


# ─────────────────────────────────────────────────────────────────────────────
# Deploy API Index (16 providers — kecil, cukup dengan lookup + TF-IDF fallback)
# ─────────────────────────────────────────────────────────────────────────────

class DeployAPIIndex:
    """
    Index kecil untuk 16 provider deploy API.
    Prioritas: exact provider name match → TF-IDF similarity fallback.
    """

    def __init__(self, csv_path: str = DEPLOY_API_CSV_PATH):
        print(f"[RAG-2] Loading deploy API data: {csv_path}")
        self.chunks = load_deploy_api_chunks(csv_path)
        # Build lookup dict (provider name → chunk)
        self.provider_map: Dict[str, Dict] = {}
        for chunk in self.chunks:
            name = chunk["metadata"]["provider"].strip().lower()
            self.provider_map[name] = chunk

        # TF-IDF fallback (untuk fuzzy match)
        texts = [c["text"] for c in self.chunks]
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2))
        self.matrix = self.vectorizer.fit_transform(texts)
        print(f"[RAG-2] Index built: {len(self.chunks)} providers")

    def get_by_providers(self, provider_names: List[str]) -> List[Dict]:
        """
        Cari deploy API info untuk daftar provider.
        Strategi: exact → normalized (no-space/no-dot) → TF-IDF fallback.
        """
        results = []
        for name in provider_names:
            normalized = name.strip().lower()
            # 1. Exact match
            if normalized in self.provider_map:
                results.append(self.provider_map[normalized])
                continue
            # 2. Normalized match (hilangkan spasi, titik, dash)
            stripped = re.sub(r"[\s\.\-_]", "", normalized)
            found = None
            for key, chunk in self.provider_map.items():
                if re.sub(r"[\s\.\-_]", "", key) == stripped:
                    found = chunk
                    break
            if found:
                print(f"[RAG-2] Normalized match '{name}' -> '{found['metadata']['provider']}'")
                results.append(found)
                continue
            # 3. Substring match
            for key, chunk in self.provider_map.items():
                if stripped in re.sub(r"[\s\.\-_]", "", key) or \
                   re.sub(r"[\s\.\-_]", "", key) in stripped:
                    found = chunk
                    break
            if found:
                print(f"[RAG-2] Substring match '{name}' -> '{found['metadata']['provider']}'")
                results.append(found)
                continue
            # 4. TF-IDF fallback
            q_vec = self.vectorizer.transform([name])
            scores = cosine_similarity(q_vec, self.matrix).flatten()
            best_idx = int(np.argmax(scores))
            if scores[best_idx] > 0.05:
                matched = self.chunks[best_idx]
                print(f"[RAG-2] TF-IDF match '{name}' -> "
                      f"'{matched['metadata']['provider']}' (score={scores[best_idx]:.2f})")
                results.append(matched)
            else:
                print(f"[RAG-2] Warning: no match found for provider '{name}'")
        return results

    def search_by_text(self, query: str, top_k: int = RAG2_TOP_K) -> List[Dict]:
        """TF-IDF search by free-form query (untuk mode tanpa JSON input)."""
        q_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(q_vec, self.matrix).flatten()
        top_idx = np.argsort(scores)[::-1][:top_k]
        return [self.chunks[i] for i in top_idx if scores[i] > 0]


# ─────────────────────────────────────────────────────────────────────────────
# RAG System 2 — Deploy Code Generator
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT_DEPLOY = """
You are DeployBuddy's Deploy Code Generator AI.

Your job: given a deployment specification JSON and real provider API documentation,
generate production-ready Python deployment code.

You MUST output THREE sections, each in a clearly labelled code block:

────────────────────────────────────────────────────────────────────────────
[FILE: deploy.py]
```python
# Full Python deployment script using the provider's API or SDK.
# Requirements:
# - Use requests or official SDK (boto3, google-cloud-*, etc.)
# - Read ALL credentials from environment variables (never hardcode)
# - For each provider in the spec, implement:
#     deploy_<provider_lowercase>() function
# - Main function calls all deploy functions in correct order
# - Include basic error handling and print status messages
# - Add docstring explaining what the script does
```

────────────────────────────────────────────────────────────────────────────
[FILE: .env.example]
```env
# Copy this to .env and fill in your actual credentials.
# NEVER commit .env to version control.
# <PROVIDER>_<KEY>=your_value_here
```

────────────────────────────────────────────────────────────────────────────
[FILE: DEPLOY_README.md]
```markdown
# DeployBuddy — Deployment Guide

## Prerequisites
...

## Step-by-step Manual Deployment
...

## Running Auto Deploy Script
...

## Rollback
...
```

Base ALL code strictly on the API documentation provided in the CONTEXT.
Do not invent API endpoints or SDK calls not present in the docs.
"""


class DeployCodeRAG:
    """
    RAG System 2: Generate Python deployment code dari JSON spec + API docs.

    Usage:
        # Cara 1: dari hasil RAG System 1 (rekomendasi)
        deployer = DeployCodeRAG()
        result = deployer.generate_from_arch_result(arch_result)

        # Cara 2: dari JSON langsung
        result = deployer.generate_from_json(deploy_json)

        # Cara 3: dari daftar provider nama saja
        result = deployer.generate_from_providers(["AWS", "Supabase"])

        # Output files
        result.save_files("./output/")
    """

    def __init__(self, llm_provider: str = None, csv_path: str = DEPLOY_API_CSV_PATH):
        self.index = DeployAPIIndex(csv_path)
        self.llm   = LLMClient(provider=llm_provider)

    def _build_context(self, api_chunks: List[Dict]) -> str:
        """Susun API docs menjadi context block untuk prompt."""
        parts = ["=== PROVIDER DEPLOY API DOCUMENTATION (retrieved) ==="]
        for chunk in api_chunks:
            parts.append(deploy_api_chunk_to_context(chunk))
        return "\n".join(parts)

    def _build_user_message(
        self,
        context: str,
        deploy_json: Optional[Dict],
        provider_names: List[str],
    ) -> str:
        import json
        if deploy_json:
            json_str = json.dumps(deploy_json, indent=2)
        else:
            provider_list = ", ".join(
                '{"provider": "' + p + '"}' for p in provider_names
            )
            json_str = '{"providers": [' + provider_list + ']}'
        return f"""
CONTEXT:
{context}

---
DEPLOYMENT SPEC (from Architecture RAG):
```json
{json_str}
```

Using ONLY the API documentation in the CONTEXT above, generate:
1. deploy.py  — complete Python script to deploy all services in the spec
2. .env.example — all required environment variables
3. DEPLOY_README.md — step-by-step manual + auto-deploy guide
"""

    def _parse_files(self, llm_response: str) -> Dict[str, str]:
        """
        Parse tiga file dari response LLM.
        Return dict: {filename: content}
        """
        files = {}

        # deploy.py
        py_match = re.search(r"\[FILE: deploy\.py\].*?```python\s*([\s\S]*?)```", llm_response)
        if py_match:
            files["deploy.py"] = py_match.group(1).strip()

        # .env.example
        env_match = re.search(r"\[FILE: \.env\.example\].*?```env\s*([\s\S]*?)```", llm_response)
        if env_match:
            files[".env.example"] = env_match.group(1).strip()

        # DEPLOY_README.md
        readme_match = re.search(r"\[FILE: DEPLOY_README\.md\].*?```markdown\s*([\s\S]*?)```", llm_response)
        if readme_match:
            files["DEPLOY_README.md"] = readme_match.group(1).strip()

        return files

    def _run_retrieval(self, provider_names: List[str]) -> List[Dict]:
        """Ambil deploy API docs untuk provider-provider yang dipilih."""
        print(f"[RAG-2] Looking up providers: {provider_names}")
        chunks = self.index.get_by_providers(provider_names)
        print(f"[RAG-2] Retrieved {len(chunks)} API doc entries")
        return chunks

    # ── Public interface ──────────────────────────────────────────────────────

    def generate_from_arch_result(self, arch_result) -> "DeployCodeResult":
        """Terima ArchitectureResult langsung dari RAG System 1."""
        provider_names = arch_result.get_provider_names()
        return self.generate_from_json(arch_result.deploy_json, provider_names)

    def generate_from_json(
        self,
        deploy_json: Dict,
        provider_names: Optional[List[str]] = None,
    ) -> "DeployCodeResult":
        """Generate dari dict JSON deployment spec."""
        if provider_names is None:
            provider_names = list({p["provider"] for p in deploy_json.get("providers", [])})
        return self._generate(deploy_json, provider_names)

    def generate_from_providers(self, provider_names: List[str]) -> "DeployCodeResult":
        """Generate hanya dari daftar nama provider (tanpa JSON spec)."""
        return self._generate(None, provider_names)

    def _generate(
        self,
        deploy_json: Optional[Dict],
        provider_names: List[str],
    ) -> "DeployCodeResult":
        # Step 1: Retrieve API docs
        api_chunks = self._run_retrieval(provider_names)
        if not api_chunks:
            raise ValueError(f"No deploy API data found for: {provider_names}")

        # Step 2: Build context
        context = self._build_context(api_chunks)

        # Step 3: Build user message
        user_message = self._build_user_message(context, deploy_json, provider_names)

        # Step 4: LLM call
        print("[RAG-2] Calling LLM to generate deployment code...")
        llm_response = self.llm.chat(SYSTEM_PROMPT_DEPLOY, user_message)

        # Step 5: Parse files
        files = self._parse_files(llm_response)
        print(f"[RAG-2] Generated files: {list(files.keys())}")

        return DeployCodeResult(
            raw_response=llm_response,
            files=files,
            retrieved_chunks=api_chunks,
        )


class DeployCodeResult:
    """Container untuk hasil RAG System 2."""

    def __init__(self, raw_response: str, files: Dict[str, str], retrieved_chunks: List[Dict]):
        self.raw_response      = raw_response
        self.files             = files          # {"deploy.py": "...", ".env.example": "...", ...}
        self.retrieved_chunks  = retrieved_chunks

    def save_files(self, output_dir: str = "./output"):
        """Simpan semua generated files ke disk."""
        import os
        os.makedirs(output_dir, exist_ok=True)
        for filename, content in self.files.items():
            path = os.path.join(output_dir, filename)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[RAG-2] Saved: {path}")

    def print_summary(self):
        print("\n" + "="*70)
        print("DEPLOYBUDDY - GENERATED DEPLOYMENT CODE")
        print("="*70)
        print(self.raw_response)
        if self.files:
            print(f"\n[Generated {len(self.files)} files: {list(self.files.keys())}]")
