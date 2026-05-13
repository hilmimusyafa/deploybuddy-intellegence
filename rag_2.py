import json
import os
import re
from llm_client import LLMClient

class DeploymentCodeRAG:
    def __init__(self, deploy_col, llm_client: LLMClient):
        self.deploy_col = deploy_col
        self.llm = llm_client

    def generate_code(self, deployment_plan: dict, provider: str) -> str:
        """
        deployment_plan: dict dari RAG-1 (berisi instance_type, region, dll)
        provider: nama provider
        """
        if not provider:
            raise ValueError("Provider kosong. RAG-2 hanya boleh berjalan setelah RAG-1 menghasilkan provider valid.")

        # --- 1. Retrieve detail deploy untuk provider ini ---
        query = f"Provider: {provider} deploy flow API endpoint auth method secrets"
        n_results = self._env_int("RAG2_TOP_K", 1)
        try:
            results = self.deploy_col.query(
                query_texts=[query],
                n_results=max(1, min(n_results, 3)),
                where={"provider": provider},
            )
        except Exception:
            results = self.deploy_col.query(query_texts=[query], n_results=max(1, min(n_results, 3)))

        documents = results.get("documents") or [[]]
        deploy_docs = documents[0] if documents and documents[0] else []
        deploy_context = "\n---\n".join(deploy_docs)
        if not deploy_context.strip():
            deploy_context = (
                f"No deployment API context was retrieved for {provider}. "
                "Generated files must stay generic and mark provider API calls as TODO."
            )

        # --- 2. Prompt untuk menghasilkan paket draft deployment ---
        prompt = f"""You are a DevOps expert. I have a deployment plan for provider '{provider}':
        
        Deployment Plan:
        {json.dumps(deployment_plan, indent=2)}

        Here is the official deployment API/SDK information:
        {deploy_context}

        Anti-hallucination constraints:
        - Use only the provider shown in the deployment API context.
        - Do not call APIs, SDK methods, resources, or auth secrets that are not present in the context.
        - If an exact API endpoint or SDK call is missing from the context, add a clear TODO comment instead of inventing it.
        - Do not deploy supporting database/BaaS services unless they are explicitly present in the deployment_plan.
        - Do not include hidden reasoning, chain-of-thought, or <think> tags.

        Write a deployment package in Markdown, not a prose essay.
        Include these sections when relevant to the plan:
        1. FILE: Dockerfile
        2. FILE: docker-compose.yml
        3. FILE: .github/workflows/deploy.yml
        4. FILE: .env.example
        5. FILE: deploy.py (only if provider API/SDK context is sufficient)
        6. GUIDE: provider-specific manual deployment steps
        7. VERIFY: commands or checks to confirm deployment success

        For each FILE section, include a fenced code block with the exact suggested file content.
        Use required secrets from environment variables, never hard-code credentials.
        Output only the Markdown deployment package."""

        return self._clean_markdown(self.llm.generate(prompt, max_tokens=3200))

    def _clean_markdown(self, output: str) -> str:
        clean = re.sub(r"<think>.*?</think>", "", output, flags=re.DOTALL | re.IGNORECASE).strip()
        if clean.startswith("```markdown"):
            clean = clean.split("```markdown", 1)[1]
            if "```" in clean:
                clean = clean.rsplit("```", 1)[0]
        return clean.strip()

    def _env_int(self, name: str, default: int) -> int:
        try:
            return int(os.getenv(name, str(default)))
        except ValueError:
            return default
