import json

class ArchitectureRAG:
    def __init__(self, pricing_col, deploy_col, llm_client: LLMClient):
        self.pricing_col = pricing_col
        self.deploy_col = deploy_col
        self.llm = llm_client

    def recommend(self, tech_stack: dict, user_prefs: dict) -> dict:
        """
        tech_stack: hasil deteksi stack, mis.
            {"language": "Python", "framework": "FastAPI", "database": "PostgreSQL", "type": "backend"}
        user_prefs: {"budget_monthly_usd": 30, "target_ccu": 100, "target_regions": ["Asia Tenggara"], "service_type": "web_backend"}
        """
        # --- 1. Buat query dari input ---
        query = (
            f"Provider for {tech_stack.get('language','')} {tech_stack.get('framework','')} "
            f"with {tech_stack.get('database','')} database. "
            f"Target region: {', '.join(user_prefs.get('target_regions',[]))}. "
            f"Budget monthly around {user_prefs.get('budget_monthly_usd','')} USD. "
            f"Expected concurrent users: {user_prefs.get('target_ccu','')}. "
            f"Service type: {user_prefs.get('service_type','')}. "
            f"Low maintenance preferred."
        )

        # --- 2. Retrieve relevant pricing & deploy info ---
        pricing_results = self.pricing_col.query(query_texts=[query], n_results=8)
        deploy_results = self.deploy_col.query(query_texts=[query], n_results=3)

        pricing_context = "\n---\n".join(pricing_results['documents'][0])
        deploy_context = "\n---\n".join(deploy_results['documents'][0])

        # --- 3. Bangun prompt untuk LLM ---
        prompt = f"""You are an expert cloud deployment architect.

        I have the following tech stack details:
        {json.dumps(tech_stack, indent=2)}

        User preferences:
        {json.dumps(user_prefs, indent=2)}

        Here is relevant pricing data from various providers:
        {pricing_context}

        Here is deployment API details for those providers:
        {deploy_context}

        Based on the above, provide a comprehensive deployment recommendation with the following structure:

        OUTPUT A VALID JSON OBJECT with these keys:
        {{
        "architecture_diagram": "Mermaid diagram code (string) illustrating the architecture",
        "provider": "selected_provider_name",
        "service_model": "VM/Container/Serverless etc.",
        "region": "recommended region",
        "resource_spec": {{"cpu": ..., "ram_gb": ..., "storage_gb": ..., "gpu": ...}},
        "estimated_monthly_cost_usd": number,
        "guide": "step-by-step manual deployment guide in markdown (string with \\n for newlines)",
        "deployment_plan": {{ ... object containing all needed parameters for automated deploy, e.g. instance_type, secrets, region, etc. }},
        "risk_notes": "string about potential pitfalls"
        }}

        Ensure the JSON is valid without any additional text before or after."""
        
        # --- 4. Panggil LLM ---
        response_text = self.llm.generate(prompt, max_tokens=2500)
        
        # --- 5. Parse JSON output (dengan pembersihan) ---
        try:
            clean = response_text.strip()
            # Mencari JSON object dengan mencari kurung kurawal pertama dan terakhir
            start_idx = clean.find('{')
            end_idx = clean.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                clean = clean[start_idx:end_idx+1]
            
            import re
            # Buang karakter control atau newlines di dalam string diagram markdown
            clean = re.sub(r'```mermaid.*?```', 'mermaid diagram omitted', clean, flags=re.DOTALL)
            # Hilangkan trailing comma yang sering menjadi penyebab invalid JSON
            clean = re.sub(r',\s*\}', '}', clean)
            clean = re.sub(r',\s*\]', ']', clean)
            
            return json.loads(clean)
        except json.JSONDecodeError as e:
            # Jika JSON.loads masih gagal, gunakan Regex Fallback untuk memaksa mengekstrak plan demi RAG-2
            fallback = {"raw_output": response_text, "error": f"Could not parse JSON: {str(e)}"}
            import re
            
            provider_match = re.search(r'"provider"\s*:\s*"([^"]+)"', clean)
            if provider_match:
                fallback["provider"] = provider_match.group(1)
                
            # Coba ambil isi blok deployment_plan
            plan_match = re.search(r'"deployment_plan"\s*:\s*(\{.*?\})', clean, re.DOTALL)
            if plan_match:
                fallback["deployment_plan"] = plan_match.group(1) # Sengaja disimpan sebagai string
                
            return fallback