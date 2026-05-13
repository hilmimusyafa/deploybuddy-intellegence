import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from deploybuddy import _profile_to_tech_stack, _resolve_service_type, _guardrail_blocks_rag2
from llm_client import get_llm_client_from_env
from repository_analyzer import RepositoryAnalysisError, analyze_repository


load_dotenv()

app = FastAPI(title="DeployBuddy API", version="0.1.0")

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_conversations: Dict[str, Dict[str, Any]] = {}
_tokens: Dict[str, Dict[str, Any]] = {}
_rag_cache: Dict[str, Any] = {}


class ConversationCreate(BaseModel):
    title: str = "New deployment conversation"
    messages: List[Dict[str, Any]] = Field(default_factory=list)


class TokenPayload(BaseModel):
    value: str
    provider: Optional[str] = None
    label: Optional[str] = None


class DeployRequest(BaseModel):
    repo_url: Optional[str] = None
    repo_path: Optional[str] = None
    budget: int = 30
    ccu: int = 200
    region: str = "Indonesia"
    service_type: str = "auto"
    max_snippets: int = 2
    user_message: Optional[str] = None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_repo_url(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    repo = value.strip()
    if repo.startswith("github.com/"):
        return f"https://{repo}"
    return repo


def _target_regions(region: str) -> List[str]:
    cleaned = (region or "Indonesia").strip()
    regions = [cleaned]
    if cleaned.lower() == "indonesia":
        regions.append("Asia Tenggara")
    return regions


def _get_rag_components():
    if _rag_cache:
        return _rag_cache["backend"], _rag_cache["rag1"], _rag_cache["rag2"]

    backend, llm = get_llm_client_from_env()
    from rag_1 import ArchitectureRAG
    from rag_2 import DeploymentCodeRAG
    from stores import collection_deploy, collection_pricing

    _rag_cache["backend"] = backend
    _rag_cache["rag1"] = ArchitectureRAG(collection_pricing, collection_deploy, llm)
    _rag_cache["rag2"] = DeploymentCodeRAG(collection_deploy, llm)
    return _rag_cache["backend"], _rag_cache["rag1"], _rag_cache["rag2"]


def _mask_secret(value: str) -> str:
    if len(value) <= 8:
        return "********"
    return f"{value[:4]}{'*' * 8}{value[-4:]}"


def _resource_text(resource_spec: Any) -> str:
    if not isinstance(resource_spec, dict):
        return "Unknown resources"
    cpu = str(resource_spec.get("cpu", "unknown CPU"))
    ram = resource_spec.get("ram_gb", "unknown RAM")
    storage = resource_spec.get("storage_gb", "unknown storage")
    gpu = resource_spec.get("gpu")
    cpu_text = cpu if "cpu" in cpu.lower() else f"{cpu} CPU"
    parts = [cpu_text, f"{ram} GB RAM", f"{storage} GB storage"]
    if gpu and str(gpu).lower() not in {"none", "unknown", "n/a"}:
        parts.append(f"{gpu} GPU")
    return " / ".join(parts)


def _risk_level(recommendation: Dict[str, Any]) -> str:
    guardrail = recommendation.get("guardrail")
    if isinstance(guardrail, dict) and guardrail.get("is_valid") is False:
        return "high"
    confidence = str(recommendation.get("confidence", "")).lower()
    if confidence == "low":
        return "medium"
    risk_notes = str(recommendation.get("risk_notes", "")).strip()
    return "medium" if risk_notes else "low"


def _ui_recommendation(profile_json: Dict[str, Any], recommendation: Dict[str, Any], budget: int) -> Dict[str, Any]:
    cost = recommendation.get("estimated_monthly_cost_usd")
    try:
        monthly_cost = float(cost)
    except (TypeError, ValueError):
        monthly_cost = 0.0

    provider = str(recommendation.get("provider", "Unknown provider"))
    supporting = recommendation.get("supporting_services", [])
    supporting_names = []
    if isinstance(supporting, list):
        for item in supporting:
            if isinstance(item, dict) and item.get("provider"):
                supporting_names.append(f"{item['provider']} ({item.get('role', 'supporting')})")

    alternatives = []
    matrix = recommendation.get("provider_comparison_matrix", [])
    if isinstance(matrix, list):
        for item in matrix:
            if not isinstance(item, dict) or item.get("provider") == provider:
                continue
            alternatives.append(
                {
                    "provider": str(item.get("provider", "Alternative")),
                    "architecture": str(item.get("fit_reason", item.get("category", "Alternative deployment"))),
                    "monthly_estimate": f"${item.get('estimated_monthly_cost_usd', '?')}/mo",
                    "pros": [str(item.get("fit_reason", "Fits this workload"))],
                    "cons": [str(item.get("tradeoff", "Review provider limitations"))],
                    "best_for": str(item.get("category", "similar workloads")),
                }
            )

    risk = str(recommendation.get("risk_notes", "Review generated deployment package before production use."))
    within_budget = monthly_cost <= budget if monthly_cost else True
    return {
        "stack_detected": profile_json.get("detected_stack", []),
        "architecture": str(recommendation.get("service_model", "Deployment architecture")),
        "providers": " + ".join([provider, *supporting_names]) if supporting_names else provider,
        "region": str(recommendation.get("region", "Indonesia")),
        "resources": _resource_text(recommendation.get("resource_spec")),
        "deployment_type": str(recommendation.get("provider_category", "unknown")),
        "risk": risk[:180],
        "risk_level": _risk_level(recommendation),
        "summary": f"Recommended {provider} for this repository based on detected stack, budget, region, and provider guardrails.",
        "warning": None if within_budget else f"Estimated cost exceeds the ${budget}/mo budget.",
        "estimated_cost": {
            "monthly_min": round(monthly_cost, 2),
            "monthly_max": round(monthly_cost, 2),
            "currency": "USD",
            "breakdown": [{"item": provider, "cost": f"${round(monthly_cost, 2)}/mo"}],
            "within_budget": within_budget,
            "budget_note": "Within target budget." if within_budget else "Over the configured target budget.",
        },
        "alternatives": alternatives[:3],
        "feasibility": {
            "budget": 85 if within_budget else 45,
            "scalability": 75,
            "reliability": 75,
            "ease_of_setup": 80 if recommendation.get("deployment_plan") else 55,
        },
        "deployment_package": recommendation.get("deployment_package"),
    }


@app.get("/")
def get_conversations():
    return {"conversations": list(_conversations.values())}


@app.get("/conversation/{conversation_id}")
def get_conversation(conversation_id: str):
    conversation = _conversations.get(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@app.post("/conversation")
def create_conversation(payload: ConversationCreate):
    conversation_id = str(uuid.uuid4())
    conversation = {
        "id": conversation_id,
        "title": payload.title,
        "messages": payload.messages,
        "created_at": _utc_now(),
        "updated_at": _utc_now(),
    }
    _conversations[conversation_id] = conversation
    return conversation


@app.delete("/conversation/{conversation_id}")
def delete_conversation(conversation_id: str):
    if conversation_id not in _conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"deleted": _conversations.pop(conversation_id)}


@app.get("/token")
def get_tokens():
    return {
        "tokens": [
            {**token, "value": _mask_secret(token["value"])}
            for token in _tokens.values()
        ]
    }


@app.post("/token/{token_id}")
def add_token(token_id: str, payload: TokenPayload):
    _tokens[token_id] = {
        "id": token_id,
        "provider": payload.provider,
        "label": payload.label,
        "value": payload.value,
        "created_at": _utc_now(),
        "updated_at": _utc_now(),
    }
    return {**_tokens[token_id], "value": _mask_secret(payload.value)}


@app.put("/token/{token_id}")
def update_token(token_id: str, payload: TokenPayload):
    if token_id not in _tokens:
        raise HTTPException(status_code=404, detail="Token not found")
    _tokens[token_id].update(
        {
            "provider": payload.provider,
            "label": payload.label,
            "value": payload.value,
            "updated_at": _utc_now(),
        }
    )
    return {**_tokens[token_id], "value": _mask_secret(payload.value)}


@app.delete("/token/{token_id}")
def delete_token(token_id: str):
    if token_id not in _tokens:
        raise HTTPException(status_code=404, detail="Token not found")
    token = _tokens.pop(token_id)
    return {**token, "value": _mask_secret(token["value"])}


@app.post("/deploy")
def deploy(payload: DeployRequest):
    repo_url = _normalize_repo_url(payload.repo_url)
    repo_path = payload.repo_path
    if not repo_url and not repo_path:
        raise HTTPException(status_code=400, detail="repo_url or repo_path is required")

    try:
        profile = analyze_repository(
            repo_url=repo_url,
            repo_path=repo_path,
            max_files=15,
            max_snippets=payload.max_snippets,
        )
    except RepositoryAnalysisError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        backend, rag1, rag2 = _get_rag_components()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to initialize LLM backend: {exc}") from exc

    tech_stack = _profile_to_tech_stack(profile)
    service_type = _resolve_service_type(profile, payload.service_type)
    user_prefs = {
        "budget_monthly_usd": payload.budget,
        "target_ccu": payload.ccu,
        "target_regions": _target_regions(payload.region),
        "service_type": service_type,
    }

    try:
        recommendation = rag1.recommend(tech_stack, user_prefs)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"RAG-1 failed on backend '{backend}': {exc}") from exc

    block_reason = _guardrail_blocks_rag2(recommendation)
    if block_reason:
        raise HTTPException(status_code=422, detail=block_reason)

    provider = str(recommendation["provider"])
    try:
        deployment_package = rag2.generate_code(recommendation["deployment_plan"], provider)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"RAG-2 failed on backend '{backend}': {exc}") from exc

    recommendation["deployment_package"] = deployment_package
    profile_json = profile.to_json()
    return {
        "repository_profile": profile_json,
        "recommendation": recommendation,
        "deployment_package": deployment_package,
        "ui_recommendation": _ui_recommendation(profile_json, recommendation, payload.budget),
    }
