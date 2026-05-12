import json
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
        # --- 1. Retrieve detail deploy untuk provider ini ---
        query = f"Provider: {provider} deploy flow API endpoint auth method secrets"
        results = self.deploy_col.query(query_texts=[query], n_results=2)
        deploy_context = "\n---\n".join(results['documents'][0])

        # --- 2. Prompt untuk menghasilkan kode Python ---
        prompt = f"""You are a DevOps expert. I have a deployment plan for provider '{provider}':
        
        Deployment Plan:
        {json.dumps(deployment_plan, indent=2)}

        Here is the official deployment API/SDK information:
        {deploy_context}

        Write a Python script that uses the provider's API (REST or SDK) to deploy the resources according to the plan.
        Include all necessary steps: authentication, resource creation, waiting for readiness, and printing the result.
        Use the required secrets from environment variables (e.g., os.getenv()).
        Output only the Python code, no additional explanation."""
        
        code = self.llm.generate(prompt, max_tokens=2500)
        # Bersihkan jika ada markdown code block
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        elif "```" in code:
            code = code.split("```")[1].split("```")[0]
        return code