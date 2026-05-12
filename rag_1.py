import csv
import json
import os
import re
from pathlib import Path

from llm_client import LLMClient


PRIMARY_WORKLOAD_RULES = {
    "backend": {
        "allowed_categories": ["backend", "cloud_major"],
        "description": "API/backend/worker compute. Database/BaaS providers can only be supporting services.",
    },
    "frontend": {
        "allowed_categories": ["web_instant", "cloud_major"],
        "description": "Static frontend or frontend app hosting.",
    },
    "web_application": {
        "allowed_categories": ["web_instant", "backend", "cloud_major"],
        "description": "Full-stack web application. Pick compute/hosting provider as primary, database as supporting service.",
    },
    "database": {
        "allowed_categories": ["database", "cloud_major"],
        "description": "Managed database or backend-as-a-service requirement.",
    },
    "ml": {
        "allowed_categories": ["ml_best", "cloud_major"],
        "description": "ML inference, model endpoint, GPU, or batch model workload.",
    },
}

DATABASE_ONLY_CATEGORIES = {"database"}


class ArchitectureRAG:
    def __init__(self, pricing_col, deploy_col, llm_client: LLMClient):
        self.pricing_col = pricing_col
        self.deploy_col = deploy_col
        self.llm = llm_client
        self.provider_catalog = self._load_provider_catalog()
        self.pricing_top_k = min(self._env_int("RAG1_TOP_K", 5), 8)
        self.deploy_top_k = min(self._env_int("RAG2_TOP_K", 2), 4)

    def recommend(self, tech_stack: dict, user_prefs: dict) -> dict:
        """
        tech_stack: hasil deteksi stack, mis.
            {"language": "Python", "framework": "FastAPI", "database": "PostgreSQL", "type": "backend"}
        user_prefs: {"budget_monthly_usd": 30, "target_ccu": 100, "target_regions": ["Asia Tenggara"], "service_type": "web_backend"}
        """
        primary_workload = self._infer_primary_workload(tech_stack, user_prefs)
        rule = PRIMARY_WORKLOAD_RULES[primary_workload]
        allowed_categories = rule["allowed_categories"]
        eligible_providers = self._eligible_providers(allowed_categories)

        # --- 1. Buat query dari input ---
        query = (
            f"Provider for {tech_stack.get('language','')} {tech_stack.get('framework','')} "
            f"with {tech_stack.get('database','')} database. "
            f"Primary workload: {primary_workload}. "
            f"Allowed provider categories: {', '.join(allowed_categories)}. "
            f"Target region: {', '.join(user_prefs.get('target_regions',[]))}. "
            f"Budget monthly around {user_prefs.get('budget_monthly_usd','')} USD. "
            f"Expected concurrent users: {user_prefs.get('target_ccu','')}. "
            f"Service type: {user_prefs.get('service_type','')}. "
            f"Low maintenance preferred."
        )

        # --- 2. Retrieve relevant pricing & deploy info sesuai role provider ---
        pricing_results = self._safe_query(
            self.pricing_col,
            query,
            n_results=self.pricing_top_k,
            allowed_categories=allowed_categories,
        )
        deploy_results = self._safe_query(
            self.deploy_col,
            query,
            n_results=max(2, min(self.deploy_top_k, len(eligible_providers) or 2)),
            allowed_categories=allowed_categories,
        )

        pricing_context = self._limit_context("\n---\n".join(pricing_results.get("documents", [[]])[0]))
        deploy_context = self._limit_context("\n---\n".join(deploy_results.get("documents", [[]])[0]))
        provider_policy = self._provider_policy_text(primary_workload, eligible_providers)

        # --- 3. Bangun prompt untuk LLM ---
        prompt = f"""You are an expert cloud deployment architect.

You must be conservative and grounded in the retrieved provider data.
Do not invent capabilities, APIs, prices, regions, or provider roles that are not present in the context.
Do not include hidden reasoning, chain-of-thought, markdown fences, or <think> tags. Return only the final JSON object.

Primary workload classification:
{primary_workload} - {rule["description"]}

Provider eligibility policy:
{provider_policy}

Important anti-hallucination rules:
1. The top-level "provider" must be a primary deployment/compute/hosting provider from the eligible provider list.
2. For backend/API/worker compute workloads, database/BaaS providers such as Supabase, Neon, MongoDB, and Firebase are not valid primary backend compute providers. They may only appear in "supporting_services" for database/auth/storage if the stack needs them.
3. If the retrieved data is insufficient, say so in "risk_notes" and choose the safest eligible provider from the provided context. Never use unsupported providers.
4. Every chosen provider role must match its category and deploy target from the deployment API context.

I have the following tech stack details:
{json.dumps(tech_stack, indent=2)}

User preferences:
{json.dumps(user_prefs, indent=2)}

Relevant pricing data from eligible provider categories:
{pricing_context}

Relevant deployment API details from eligible provider categories:
{deploy_context}

Based on the above, provide a deployment recommendation.

OUTPUT A VALID JSON OBJECT with these keys:
{{
  "architecture_diagram": "Mermaid diagram code (string) illustrating the architecture",
  "detected_repository_profile": {{
    "language": "detected runtime/language summary",
    "framework": "detected framework summary",
    "database": "detected database summary",
    "type": "detected service type summary",
    "architecture_hints": ["grounded hints from repository analysis"]
  }},
  "provider": "selected_primary_provider_name_from_eligible_list",
  "provider_category": "category from provider eligibility list",
  "service_model": "VM/Container/Serverless/etc.",
  "region": "recommended region",
  "resource_spec": {{"cpu": "...", "ram_gb": "...", "storage_gb": "...", "gpu": "..."}},
  "estimated_monthly_cost_usd": number,
  "provider_comparison_matrix": [
    {{
      "provider": "provider_name",
      "category": "provider category",
      "estimated_monthly_cost_usd": number,
      "maintenance_effort": "low|medium|high",
      "scalability": "low|medium|high",
      "fit_reason": "short grounded reason",
      "tradeoff": "main risk or limitation"
    }}
  ],
  "supporting_services": [
    {{"provider": "provider_name", "role": "database/auth/storage/etc.", "reason": "why this is supporting, not primary"}}
  ],
  "guide": "step-by-step manual deployment guide in markdown (string with \\n for newlines)",
  "deployment_plan": {{ "...": "object containing needed parameters for automated deploy" }},
  "risk_notes": "string about limitations, assumptions, and data gaps",
  "confidence": "high|medium|low"
}}

Ensure the JSON is valid without any additional text before or after."""

        # --- 4. Panggil LLM ---
        response_text = self.llm.generate(prompt, max_tokens=800)

        # --- 5. Parse dan validasi output ---
        plan = self._parse_plan(response_text)
        plan = self._repair_if_invalid(
            plan=plan,
            original_response=response_text,
            primary_workload=primary_workload,
            eligible_providers=eligible_providers,
            provider_policy=provider_policy,
            tech_stack=tech_stack,
            user_prefs=user_prefs,
        )
        return plan

    def _load_provider_catalog(self) -> list[dict]:
        csv_path = Path(__file__).with_name("provider_deploy_api.csv")
        with csv_path.open(newline="", encoding="utf-8") as file:
            return list(csv.DictReader(file))

    def _infer_primary_workload(self, tech_stack: dict, user_prefs: dict) -> str:
        text = " ".join(
            str(value)
            for value in [
                tech_stack.get("language", ""),
                tech_stack.get("framework", ""),
                tech_stack.get("database", ""),
                tech_stack.get("type", ""),
                user_prefs.get("service_type", ""),
            ]
        ).lower()

        backend_terms = [
            "api",
            "backend",
            "fastapi",
            "django",
            "flask",
            "express",
            "nestjs",
            "spring",
            "laravel",
            "golang",
            "go",
            "worker",
        ]
        frontend_terms = ["frontend", "static", "react", "vue", "svelte", "vite"]
        fullstack_terms = ["next.js", "nextjs", "nuxt", "web_application", "web application"]
        database_terms = ["database", "postgres", "mysql", "mongodb", "supabase", "neon", "firebase"]
        ml_terms = ["ml", "machine learning", "model", "inference", "gpu", "pytorch", "tensorflow"]

        if any(term in text for term in ml_terms):
            return "ml"
        if any(term in text for term in backend_terms):
            return "backend"
        if any(term in text for term in fullstack_terms):
            return "web_application"
        if any(term in text for term in frontend_terms):
            return "frontend"
        if any(term in text for term in database_terms):
            return "database"
        return "web_application"

    def _eligible_providers(self, allowed_categories: list[str]) -> list[dict]:
        return [
            {
                "provider": row["provider"],
                "category": row["category"],
                "deploy_target": row["deploy_target"],
                "api_type": row["api_type"],
            }
            for row in self.provider_catalog
            if row.get("category") in allowed_categories
        ]

    def _provider_policy_text(self, primary_workload: str, eligible_providers: list[dict]) -> str:
        eligible_lines = [
            f"- {row['provider']} | category={row['category']} | deploy_target={row['deploy_target']} | api={row['api_type']}"
            for row in eligible_providers
        ]

        excluded = [
            f"- {row['provider']} | category={row['category']} | deploy_target={row['deploy_target']}"
            for row in self.provider_catalog
            if row.get("category") in DATABASE_ONLY_CATEGORIES and primary_workload != "database"
        ]

        parts = ["Eligible primary providers:", *eligible_lines]
        if excluded:
            parts.extend(
                [
                    "",
                    "Not eligible as primary provider for this workload; only allowed as supporting services:",
                    *excluded,
                ]
            )
        return "\n".join(parts)

    def _safe_query(self, collection, query: str, n_results: int, allowed_categories: list[str]) -> dict:
        try:
            return collection.query(
                query_texts=[query],
                n_results=n_results,
                where={"category": {"$in": allowed_categories}},
            )
        except Exception:
            return collection.query(query_texts=[query], n_results=n_results)

    def _parse_plan(self, response_text: str) -> dict:
        clean = response_text.strip()
        clean = re.sub(r"<think>.*?</think>", "", clean, flags=re.DOTALL | re.IGNORECASE).strip()
        start_idx = clean.find("{")
        end_idx = clean.rfind("}")

        if start_idx != -1 and end_idx != -1:
            clean = clean[start_idx : end_idx + 1]

        clean = re.sub(r"```(?:json|mermaid|markdown|python)?", "", clean)
        clean = clean.replace("```", "")
        clean = re.sub(r",\s*\}", "}", clean)
        clean = re.sub(r",\s*\]", "]", clean)

        try:
            return json.loads(clean)
        except json.JSONDecodeError as e:
            fallback = {"raw_output": clean, "error": f"Could not parse JSON: {str(e)}"}

            provider_match = re.search(r'"provider"\s*:\s*"([^"]+)"', clean)
            if provider_match:
                fallback["provider"] = provider_match.group(1)

            plan_match = re.search(r'"deployment_plan"\s*:\s*(\{.*?\})', clean, re.DOTALL)
            if plan_match:
                fallback["deployment_plan"] = plan_match.group(1)

            return fallback

    def _repair_if_invalid(
        self,
        plan: dict,
        original_response: str,
        primary_workload: str,
        eligible_providers: list[dict],
        provider_policy: str,
        tech_stack: dict,
        user_prefs: dict,
    ) -> dict:
        self._normalize_provider_fields(plan)
        validation = self._validate_provider(plan, primary_workload, eligible_providers)
        self._ensure_prd_fields(plan, tech_stack, user_prefs)
        plan["guardrail"] = validation

        if validation["is_valid"] and "error" not in plan:
            plan["provider"] = validation["provider"]
            plan["provider_category"] = validation["provider_category"]
            if isinstance(plan.get("deployment_plan"), dict):
                plan["deployment_plan"]["provider"] = validation["provider"]
                plan["deployment_plan"]["provider_category"] = validation["provider_category"]
            self._drop_debug_fields(plan)
            return plan

        repair_prompt = f"""The previous deployment recommendation violated provider eligibility rules.

Validation error:
{json.dumps(validation, indent=2)}

Primary workload:
{primary_workload}

Provider eligibility policy:
{provider_policy}

Tech stack:
{json.dumps(tech_stack, indent=2)}

User preferences:
{json.dumps(user_prefs, indent=2)}

Previous invalid response:
{original_response[:6000]}

Return a corrected VALID JSON object using only an eligible primary provider.
Move database/BaaS providers to supporting_services when appropriate.
Do not include hidden reasoning, chain-of-thought, markdown fences, or <think> tags.
Do not add any explanation outside JSON."""

        repaired_text = self.llm.generate(repair_prompt, max_tokens=800)
        repaired_plan = self._parse_plan(repaired_text)
        self._normalize_provider_fields(repaired_plan)
        repaired_validation = self._validate_provider(repaired_plan, primary_workload, eligible_providers)
        self._ensure_prd_fields(repaired_plan, tech_stack, user_prefs)
        repaired_plan["guardrail"] = repaired_validation

        if repaired_validation["is_valid"]:
            repaired_plan["provider"] = repaired_validation["provider"]
            repaired_plan["provider_category"] = repaired_validation["provider_category"]
            if isinstance(repaired_plan.get("deployment_plan"), dict):
                repaired_plan["deployment_plan"]["provider"] = repaired_validation["provider"]
                repaired_plan["deployment_plan"]["provider_category"] = repaired_validation["provider_category"]
            repaired_plan["guardrail"]["repaired"] = True
            self._drop_debug_fields(repaired_plan)
            return repaired_plan

        return self._fallback_plan(
            primary_workload=primary_workload,
            eligible_providers=eligible_providers,
            tech_stack=tech_stack,
            user_prefs=user_prefs,
            failed_validation=repaired_validation,
        )

    def _ensure_prd_fields(self, plan: dict, tech_stack: dict, user_prefs: dict | None = None) -> None:
        if not isinstance(plan, dict):
            return

        plan.setdefault(
            "detected_repository_profile",
            {
                "language": tech_stack.get("language", "Not detected"),
                "framework": tech_stack.get("framework", "Not detected"),
                "database": tech_stack.get("database", "Not detected"),
                "type": tech_stack.get("type", "Unknown"),
                "architecture_hints": tech_stack.get("architecture_hints", []),
            },
        )
        plan.setdefault("provider_comparison_matrix", [])
        plan["supporting_services"] = self._normalize_supporting_services(plan.get("supporting_services", []))
        plan.setdefault("architecture_diagram", "flowchart TD\n  User-->App\n  App-->Provider")
        plan.setdefault("service_model", self._infer_service_model_from_plan(plan))
        plan["region"] = self._normalize_region(
            plan.get("region") or self._infer_region_from_plan(plan),
            user_prefs or {},
        )
        plan.setdefault("resource_spec", self._infer_resource_spec_from_plan(plan))
        plan.setdefault("estimated_monthly_cost_usd", self._infer_cost_from_plan(plan))
        plan.setdefault("guide", "Review the deployment plan, configure required secrets, deploy to the selected provider, then verify logs and health checks.")
        plan.setdefault("risk_notes", self._infer_risk_notes_from_plan(plan))
        if plan.get("provider") and "deployment_plan" not in plan:
            plan["deployment_plan"] = {
                "provider": plan.get("provider"),
                "provider_category": plan.get("provider_category", "unknown"),
                "region": plan.get("region"),
                "service_model": plan.get("service_model"),
                "resource_spec": plan.get("resource_spec"),
                "supporting_services": plan.get("supporting_services", []),
                "notes": plan.get("risk_notes", ""),
            }
        plan.setdefault("confidence", "low")

    def _normalize_provider_fields(self, plan: dict) -> None:
        if not isinstance(plan, dict) or plan.get("provider"):
            return

        recommendation = plan.get("deployment_recommendation")
        if not isinstance(recommendation, dict):
            return

        primary = recommendation.get("primary_provider")
        if isinstance(primary, dict):
            if primary.get("name"):
                plan["provider"] = primary["name"]
            if primary.get("category"):
                plan["provider_category"] = primary["category"]
            if primary.get("deploy_target"):
                plan.setdefault("service_model", primary["deploy_target"])

        if recommendation.get("supporting_services") and not plan.get("supporting_services"):
            plan["supporting_services"] = recommendation["supporting_services"]
        if recommendation.get("deployment_notes") and not plan.get("risk_notes"):
            plan["risk_notes"] = recommendation["deployment_notes"]

    def _fallback_plan(
        self,
        primary_workload: str,
        eligible_providers: list[dict],
        tech_stack: dict,
        user_prefs: dict,
        failed_validation: dict,
    ) -> dict:
        selected = eligible_providers[0] if eligible_providers else {
            "provider": "Unknown",
            "category": "unknown",
            "deploy_target": "unknown",
        }
        region = (user_prefs.get("target_regions") or ["not specified"])[0]
        provider = selected["provider"]
        plan = {
            "architecture_diagram": "flowchart TD\n  User-->App\n  App-->Provider",
            "detected_repository_profile": {
                "language": tech_stack.get("language", "Not detected"),
                "framework": tech_stack.get("framework", "Not detected"),
                "database": tech_stack.get("database", "Not detected"),
                "type": tech_stack.get("type", "Unknown"),
                "architecture_hints": tech_stack.get("architecture_hints", []),
            },
            "provider": provider,
            "provider_category": selected["category"],
            "service_model": selected.get("deploy_target", "Container"),
            "region": region,
            "resource_spec": {"cpu": "unknown", "ram_gb": "unknown", "storage_gb": "unknown", "gpu": "unknown"},
            "estimated_monthly_cost_usd": 0,
            "provider_comparison_matrix": [
                {
                    "provider": row["provider"],
                    "category": row["category"],
                    "estimated_monthly_cost_usd": 0,
                    "maintenance_effort": "medium",
                    "scalability": "medium",
                    "fit_reason": f"Eligible {row['category']} provider for {primary_workload} workload.",
                    "tradeoff": "Fallback generated because LLM output was incomplete.",
                }
                for row in eligible_providers[:3]
            ],
            "supporting_services": [],
            "guide": "Review the detected repository profile, configure required environment variables, generate deployment files, then run a dry-run deploy before production.",
            "deployment_plan": {
                "provider": provider,
                "provider_category": selected["category"],
                "region": region,
                "service_model": selected.get("deploy_target", "Container"),
                "notes": "Deterministic fallback plan because LLM output did not satisfy the internal schema.",
            },
            "risk_notes": f"Fallback plan used because RAG-1 schema validation failed: {failed_validation.get('reason', 'unknown reason')}",
            "confidence": "low",
            "guardrail": {
                "is_valid": True,
                "reason": "Deterministic fallback selected an eligible primary provider.",
                "provider": provider,
                "provider_category": selected["category"],
                "primary_workload": primary_workload,
                "fallback": True,
                "previous_error": failed_validation,
            },
        }
        self._ensure_prd_fields(plan, tech_stack, user_prefs)
        return plan

    def _validate_provider(self, plan: dict, primary_workload: str, eligible_providers: list[dict]) -> dict:
        provider = plan.get("provider")
        eligible_by_name = {
            self._normalize_provider_name(row["provider"]): row for row in eligible_providers
        }

        if not provider:
            return {
                "is_valid": False,
                "reason": "Missing top-level provider.",
                "provider": provider,
                "eligible_providers": [row["provider"] for row in eligible_providers],
            }

        normalized = self._normalize_provider_name(provider)
        selected = eligible_by_name.get(normalized)
        if not selected:
            return {
                "is_valid": False,
                "reason": "Selected provider is not eligible as primary provider for this workload.",
                "provider": provider,
                "primary_workload": primary_workload,
                "eligible_providers": [row["provider"] for row in eligible_providers],
            }

        return {
            "is_valid": True,
            "reason": "Provider category matches primary workload.",
            "provider": selected["provider"],
            "provider_category": selected["category"],
            "primary_workload": primary_workload,
        }

    def _normalize_provider_name(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", str(value).lower())

    def _drop_debug_fields(self, plan: dict) -> None:
        plan.pop("raw_output", None)
        plan.pop("error", None)

    def _limit_context(self, context: str, max_chars: int = 650) -> str:
        if len(context) <= max_chars:
            return context
        return context[:max_chars] + "\n[Context truncated for token budget]"

    def _env_int(self, name: str, default: int) -> int:
        try:
            return int(os.getenv(name, str(default)))
        except ValueError:
            return default

    def _normalize_supporting_services(self, services) -> list:
        if not isinstance(services, list):
            return []
        normalized = []
        for service in services:
            if isinstance(service, dict):
                normalized.append(service)
            else:
                normalized.append({"provider": str(service), "role": "supporting_service", "reason": "Provided by LLM output."})
        return normalized

    def _normalize_region(self, region, user_prefs: dict) -> str:
        value = str(region or "").strip()
        target_regions = [
            str(item).strip()
            for item in user_prefs.get("target_regions", [])
            if str(item).strip()
        ]
        fallback = target_regions[0] if target_regions else "not specified"

        lowered = value.lower()
        invalid_markers = ("provider ", "category=", "api=", "deploy_target", "not specified")
        region_markers = (
            "indonesia",
            "jakarta",
            "singapore",
            "asia",
            "asia tenggara",
            "southeast",
            "ap-",
            "us-",
            "eu-",
            "af-",
            "sa-",
            "ca-",
            "me-",
        )
        looks_invalid = (
            not value
            or len(value) > 80
            or "\n" in value
            or lowered in {"aws", "gcp", "azure", "provider aws", "provider gcp"}
            or any(marker in lowered for marker in invalid_markers)
        )
        looks_like_region = any(marker in lowered for marker in region_markers)
        if looks_invalid or not looks_like_region:
            return fallback
        return value

    def _infer_service_model_from_plan(self, plan: dict) -> str:
        config = plan.get("configuration", {})
        if isinstance(config, dict) and config.get("instance_type"):
            return str(config["instance_type"])
        return "Container"

    def _infer_region_from_plan(self, plan: dict) -> str:
        config = plan.get("configuration", {})
        if isinstance(config, dict) and config.get("region"):
            return str(config["region"])
        return "not specified"

    def _infer_resource_spec_from_plan(self, plan: dict) -> dict:
        config = plan.get("configuration", {})
        if not isinstance(config, dict):
            return {"cpu": "unknown", "ram_gb": "unknown", "storage_gb": "unknown", "gpu": "unknown"}
        return {
            "cpu": str(config.get("instance_type", config.get("cpu", "unknown"))),
            "ram_gb": str(config.get("memory_gb", config.get("ram_gb", "unknown"))),
            "storage_gb": str(config.get("storage_gb", "unknown")),
            "gpu": str(config.get("gpu", "unknown")),
        }

    def _infer_cost_from_plan(self, plan: dict):
        config = plan.get("configuration", {})
        if isinstance(config, dict):
            value = config.get("cost_monthly") or config.get("estimated_monthly_cost_usd")
            if value is not None:
                match = re.search(r"\d+(?:\.\d+)?", str(value))
                if match:
                    return float(match.group(0))
        return 0

    def _infer_risk_notes_from_plan(self, plan: dict) -> str:
        constraints = plan.get("constraints", {})
        if isinstance(constraints, dict) and constraints.get("note"):
            return str(constraints["note"])
        return "LLM did not provide detailed risk notes; verify provider limits, pricing, and required secrets before deployment."
