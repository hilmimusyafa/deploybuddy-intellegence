"""
DeployBuddy — RAG System 1: Architecture & Provider Recommender
================================================================
ALUR:
  User input (stack, budget, CCU, region, service type)
       ↓
  [RETRIEVAL] TF-IDF search di provider_pricing_curated.csv
       ↓
  [INJECT] Top-K hasil disusun menjadi context block
       ↓
  [LLM INFERENCE] Prompt = System instructions + Context + User query
       ↓
  Output: Architecture summary + Provider comparison + JSON deployment spec

OUTPUT JSON schema yang dihasilkan LLM (digunakan oleh RAG System 2):
{
  "recommended_architecture": "container | serverless | vm | ...",
  "providers": [
    {
      "provider": "AWS",
      "product": "ECS on Fargate",
      "region": "ap-southeast-1",
      "plan": "0.25vCPU-0.5GB",
      "service_type": "container",
      "estimated_cost_usd": "~$15/month",
      "role": "backend"
    },
    ...
  ],
  "deployment_steps_summary": ["step 1", "step 2", ...],
  "risks": ["risk 1", ...]
}
"""

import json
import re
from typing import List, Dict, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import PRICING_CSV_PATH, RAG1_TOP_K
from data_loader import load_pricing_chunks, pricing_chunk_to_context
from llm_client import LLMClient


# ─────────────────────────────────────────────────────────────────────────────
# TF-IDF Index
# ─────────────────────────────────────────────────────────────────────────────

class PricingIndex:
    """TF-IDF index untuk 650+ baris pricing data."""

    def __init__(self, csv_path: str = PRICING_CSV_PATH):
        print(f"[RAG-1] Loading pricing data: {csv_path}")
        self.chunks = load_pricing_chunks(csv_path)
        texts = [c["text"] for c in self.chunks]

        self.vectorizer = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            max_df=0.85,
            min_df=1,
            sublinear_tf=True,
        )
        self.matrix = self.vectorizer.fit_transform(texts)
        print(f"[RAG-1] Index built: {len(self.chunks)} chunks, "
              f"vocab={len(self.vectorizer.vocabulary_)}")

    def search(self, query: str, top_k: int = RAG1_TOP_K) -> List[Dict]:
        """
        Cari top_k chunks yang paling relevan dengan query.
        Return list of {text, metadata, score}.
        """
        q_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(q_vec, self.matrix).flatten()
        top_idx = np.argsort(scores)[::-1][:top_k]
        results = []
        for idx in top_idx:
            if scores[idx] > 0:
                results.append({
                    **self.chunks[idx],
                    "score": float(scores[idx]),
                })
        return results


# ─────────────────────────────────────────────────────────────────────────────
# RAG System 1 — Architecture Recommender
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT_ARCH = """
You are DeployBuddy's Architecture AI Agent. You help developers choose the best
deployment architecture, cloud provider, and region for their application.

You have access to REAL provider pricing and product data retrieved from DeployBuddy's
knowledge base (shown in the CONTEXT block below). Always base your recommendations
on this data — do not hallucinate provider plans or prices.

Your output MUST follow this exact structure:

---
## Architecture Recommendation

[Explain the recommended architecture: monolith/microservice/serverless/container/k8s
and why it fits the user's needs. 2-3 paragraphs.]

## Provider Comparison

| Provider | Product | Region | Plan | Service Type | Est. Cost | Score |
|----------|---------|--------|------|-------------|-----------|-------|
[Fill table with top 3-5 options from the retrieved data]

## Deployment Steps (Summary)

1. [step 1]
2. [step 2]
...

## Risks & Considerations

- [risk 1]
- [risk 2]

## Deployment Spec (JSON)

```json
{
  "recommended_architecture": "<architecture type>",
  "providers": [
    {
      "provider": "<provider name>",
      "product": "<product name>",
      "region": "<region_code>",
      "plan": "<sku_or_plan>",
      "service_type": "<service_type>",
      "estimated_cost_usd": "<monthly estimate>",
      "role": "<backend|frontend|database|storage|...>"
    }
  ],
  "deployment_steps_summary": ["<step 1>", "<step 2>"],
  "risks": ["<risk 1>", "<risk 2>"]
}
```
---

If REPOSITORY ANALYSIS CONTEXT is provided:
- Treat detected repository stack as the source of truth.
- Do not recommend pure static hosting as the only target when backend/server
  runtime is detected.
- Do not invent a database when none is detected; state assumptions explicitly.
- Include a compact "repository_analysis" object in the JSON with detected_stack,
  service_types, databases, and important_files.

Always output valid JSON inside the ```json block. This JSON will be consumed by
DeployBuddy's auto-deploy module.
"""


class ArchitectureRAG:
    """
    RAG System 1: Retrieval-Augmented Generation untuk rekomendasi arsitektur.

    Usage:
        rag = ArchitectureRAG()
        result = rag.recommend(
            stack="Next.js frontend, Golang backend, PostgreSQL",
            budget_usd=50,
            concurrent_users=500,
            target_region="Southeast Asia",
            service_types=["frontend", "backend", "database"],
            extra_notes="Hackathon project, prefer free tier if possible"
        )
        print(result.text)          # full LLM response
        print(result.deploy_json)   # parsed JSON deployment spec
    """

    def __init__(self, llm_provider: str = None, csv_path: str = PRICING_CSV_PATH):
        self.index  = PricingIndex(csv_path)
        self.llm    = LLMClient(provider=llm_provider)

    def _build_query(
        self,
        stack: str,
        target_region: str,
        service_types: List[str],
        budget_usd: float,
        concurrent_users: int,
        repository_profile=None,
    ) -> str:
        """Buat query string untuk TF-IDF retrieval dari parameter user."""
        repo_stack = ""
        if repository_profile:
            repo_stack = repository_profile.to_stack_string()
        return (
            f"{repo_stack} {stack} {' '.join(service_types)} {target_region} "
            f"container serverless vm database budget {budget_usd} "
            f"concurrent users {concurrent_users}"
        )

    def _build_context(self, retrieved: List[Dict]) -> str:
        """Susun retrieved chunks menjadi context block untuk prompt."""
        lines = ["=== PROVIDER KNOWLEDGE BASE (retrieved) ==="]
        for i, chunk in enumerate(retrieved, 1):
            lines.append(f"{i}. {pricing_chunk_to_context(chunk)}")
        return "\n".join(lines)

    def _extract_json(self, llm_response: str) -> Optional[Dict]:
        """Extract JSON dari markdown code block dalam response LLM."""
        pattern = r"```json\s*([\s\S]*?)\s*```"
        matches = re.findall(pattern, llm_response)
        if not matches:
            return None
        try:
            return json.loads(matches[-1])  # ambil JSON block terakhir
        except json.JSONDecodeError as e:
            print(f"[RAG-1] JSON parse error: {e}")
            return None

    def recommend(
        self,
        stack: str,
        budget_usd: float,
        concurrent_users: int,
        target_region: str,
        service_types: List[str],
        extra_notes: str = "",
        repository_profile=None,
    ) -> "ArchitectureResult":
        """
        Main method: retrieve → inject → LLM → parse output.

        Args:
            stack:             e.g. "Next.js frontend, Golang backend, PostgreSQL"
            budget_usd:        monthly budget in USD
            concurrent_users:  expected peak concurrent users
            target_region:     e.g. "Southeast Asia", "Singapore", "US East"
            service_types:     e.g. ["frontend", "backend", "database"]
            extra_notes:       additional context from user

        Returns:
            ArchitectureResult with .text and .deploy_json
        """
        effective_stack = stack or ""
        effective_service_types = list(service_types or [])
        repository_context = ""
        repository_json_hint = ""

        if repository_profile:
            repo_stack = repository_profile.to_stack_string()
            if repo_stack:
                effective_stack = repo_stack
                if stack:
                    extra_notes = (
                        f"{extra_notes}\nUser-provided stack note/override: {stack}"
                        if extra_notes else
                        f"User-provided stack note/override: {stack}"
                    )
            for service_type in repository_profile.service_types:
                if service_type not in effective_service_types:
                    effective_service_types.append(service_type)
            repository_context = "\n\n" + repository_profile.to_context()
            repository_json_hint = json.dumps(repository_profile.to_json(), indent=2)

        if not effective_stack:
            effective_stack = "Unknown stack; infer from repository context if available"
        if not effective_service_types:
            effective_service_types = ["application"]

        # Step 1: Build retrieval query
        query = self._build_query(
            effective_stack,
            target_region,
            effective_service_types,
            budget_usd,
            concurrent_users,
            repository_profile=repository_profile,
        )
        print(f"[RAG-1] Query: {query[:100]}...")

        # Step 2: TF-IDF retrieval
        retrieved = self.index.search(query, top_k=RAG1_TOP_K)
        print(f"[RAG-1] Retrieved {len(retrieved)} chunks (top score: "
              f"{(retrieved[0]['score'] if retrieved else 0):.3f})")

        # Step 3: Build context block
        context = self._build_context(retrieved)

        # Step 4: Build user message
        user_message = f"""
CONTEXT:
{context}
{repository_context}

---
USER APPLICATION PROFILE:
- Tech Stack     : {effective_stack}
- Service Types  : {', '.join(effective_service_types)}
- Monthly Budget : ${budget_usd} USD
- Peak CCU       : {concurrent_users} concurrent users
- Target Region  : {target_region}
- Extra Notes    : {extra_notes or 'None'}

REPOSITORY PROFILE JSON (if available, use as factual application evidence):
```json
{repository_json_hint or '{}'}
```

Based ONLY on the provider data and repository analysis in the CONTEXT above,
give me the best deployment architecture recommendation with provider comparison
and JSON deployment spec.
"""
        # Step 5: LLM call
        print("[RAG-1] Calling LLM...")
        llm_response = self.llm.chat(SYSTEM_PROMPT_ARCH, user_message)

        # Step 6: Parse JSON from response
        deploy_json = self._extract_json(llm_response)

        return ArchitectureResult(
            text=llm_response,
            deploy_json=deploy_json,
            retrieved_chunks=retrieved,
            repository_profile=repository_profile,
        )


class ArchitectureResult:
    """Container untuk hasil RAG System 1."""

    def __init__(
        self,
        text: str,
        deploy_json: Optional[Dict],
        retrieved_chunks: List[Dict],
        repository_profile=None,
    ):
        self.text             = text
        self.deploy_json      = deploy_json
        self.retrieved_chunks = retrieved_chunks
        self.repository_profile = repository_profile

    def get_provider_names(self) -> List[str]:
        """Ambil daftar provider dari JSON result (input ke RAG System 2)."""
        if not self.deploy_json:
            return []
        return list({p["provider"] for p in self.deploy_json.get("providers", [])})

    def print_summary(self):
        print("\n" + "="*70)
        print("DEPLOYBUDDY - ARCHITECTURE RECOMMENDATION")
        print("="*70)
        print(self.text)
        if self.deploy_json:
            print("\n[Parsed JSON OK]")
            print(f"Providers: {self.get_provider_names()}")
        else:
            print("\n[Warning: JSON not parsed from response]")
