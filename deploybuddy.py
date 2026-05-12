import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from llm_client import get_llm_client_from_env
from repository_analyzer import RepositoryAnalysisError, RepositoryProfile, analyze_repository


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="DeployBuddy MVP CLI: repository analysis -> RAG recommendation -> deployment package"
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--repo-path", type=str, help="Path repository lokal yang akan dianalisis")
    source.add_argument("--repo-url", type=str, help="URL repository GitHub publik yang akan dianalisis")
    parser.add_argument("--budget", type=int, default=30, help="Budget bulanan target dalam USD")
    parser.add_argument("--ccu", type=int, default=200, help="Target concurrent users")
    parser.add_argument("--region", type=str, default="Indonesia", help="Target region deployment")
    parser.add_argument(
        "--service-type",
        type=str,
        default="auto",
        help="Jenis service target, misalnya web_application, backend, frontend, model, atau auto",
    )
    parser.add_argument("--max-snippets", type=int, default=2, help="Jumlah maksimal snippet kode untuk konteks RAG")
    parser.add_argument("--output", type=str, default="output", help="Folder output hasil analisis dan rekomendasi")
    return parser.parse_args()


def _profile_to_tech_stack(profile: RepositoryProfile) -> Dict[str, Any]:
    snippets_data = [f"File: {snippet.path}\n{snippet.content[:700]}" for snippet in profile.snippets]
    return {
        "language": ", ".join(profile.runtimes) if profile.runtimes else "Not detected",
        "framework": ", ".join(profile.detected_stack) if profile.detected_stack else "Not detected",
        "database": ", ".join(profile.databases) if profile.databases else "Not detected",
        "type": ", ".join(profile.service_types) if profile.service_types else "Unknown",
        "env_vars_detected": profile.env_vars_detected,
        "architecture_hints": profile.architecture_hints,
        "repository_context": profile.to_context(max_chars=1000),
        "sample_code_snippets": snippets_data,
    }


def _resolve_service_type(profile: RepositoryProfile, requested: str) -> str:
    if requested and requested.lower() != "auto":
        return requested
    if not profile.service_types:
        return "web_application"
    service_types = set(profile.service_types)
    if {"frontend", "backend"} <= service_types:
        return "web_application"
    if "backend" in service_types:
        return "backend"
    if "frontend" in service_types:
        return "frontend"
    if "model" in service_types:
        return "model"
    return profile.service_types[0]


def _build_user_prefs(args: argparse.Namespace, profile: RepositoryProfile) -> Dict[str, Any]:
    region = args.region.strip() if args.region else "Indonesia"
    target_regions: List[str] = [region]
    if region.lower() == "indonesia":
        target_regions.append("Asia Tenggara")
    return {
        "budget_monthly_usd": args.budget,
        "target_ccu": args.ccu,
        "target_regions": target_regions,
        "service_type": _resolve_service_type(profile, args.service_type),
    }


def _write_json(path: Path, payload: Dict[str, Any]):
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _guardrail_blocks_rag2(plan: Dict[str, Any]) -> Optional[str]:
    guardrail = plan.get("guardrail")
    if isinstance(guardrail, dict) and guardrail.get("is_valid") is False:
        return guardrail.get("reason") or "RAG-1 guardrail rejected the provider recommendation."
    if not plan.get("provider"):
        return "RAG-1 did not produce a primary provider."
    if not plan.get("deployment_plan"):
        return "RAG-1 did not produce a deployment_plan."
    return None


def main() -> int:
    args = _parse_args()
    output_dir = Path(args.output).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n[1/4] Menganalisis repository: {args.repo_url or args.repo_path}")
    try:
        profile = analyze_repository(
            repo_url=args.repo_url,
            repo_path=args.repo_path,
            max_files=15,
            max_snippets=args.max_snippets,
        )
    except RepositoryAnalysisError as exc:
        print(f"[ERROR] Repository analysis gagal: {exc}")
        return 1

    profile.print_summary()
    repository_profile_path = output_dir / "repository_profile.json"
    _write_json(repository_profile_path, profile.to_json())
    print(f"[OK] Repository profile disimpan: {repository_profile_path}")

    print("\n[2/4] Menyiapkan LLM dan vector store...")
    load_dotenv()
    try:
        backend, llm = get_llm_client_from_env()
    except Exception as exc:
        print(f"[ERROR] Gagal menginisialisasi LLM: {exc}")
        print("[INFO] Isi API key di .env atau jalankan: $env:LLM_PROVIDER='mock'")
        return 1

    from rag_1 import ArchitectureRAG
    from rag_2 import DeploymentCodeRAG
    from stores import collection_deploy, collection_pricing

    rag1 = ArchitectureRAG(collection_pricing, collection_deploy, llm)
    rag2 = DeploymentCodeRAG(collection_deploy, llm)

    tech_stack = _profile_to_tech_stack(profile)
    user_prefs = _build_user_prefs(args, profile)

    print(f"[3/4] Meminta rekomendasi RAG-1 via backend '{backend}'...")
    try:
        recommendation = rag1.recommend(tech_stack, user_prefs)
    except Exception as exc:
        print(f"[ERROR] RAG-1 gagal: {exc}")
        print("[INFO] Periksa API key, model/limit token, atau gunakan LLM_PROVIDER=mock untuk test offline.")
        return 1

    recommendation_path = output_dir / "recommendation.json"
    _write_json(recommendation_path, recommendation)
    print(f"[OK] Recommendation disimpan: {recommendation_path}")

    block_reason = _guardrail_blocks_rag2(recommendation)
    if block_reason:
        print(f"[STOP] RAG-2 tidak dijalankan: {block_reason}")
        return 2

    provider = str(recommendation["provider"])
    deployment_plan = recommendation["deployment_plan"]
    print(f"[4/4] Membuat deployment package RAG-2 untuk provider {provider}...")
    try:
        deployment_package = rag2.generate_code(deployment_plan, provider)
    except Exception as exc:
        print(f"[ERROR] RAG-2 gagal: {exc}")
        print("[INFO] Recommendation sudah tersimpan; ulangi dengan LLM_PROVIDER=mock jika perlu test offline.")
        return 1

    deployment_package_path = output_dir / "deployment_package.md"
    deployment_package_path.write_text(deployment_package, encoding="utf-8")
    print(f"[OK] Deployment package disimpan: {deployment_package_path}")

    guardrail = recommendation.get("guardrail", {})
    print("\n=== DeployBuddy MVP Summary ===")
    print(f"Provider : {provider}")
    print(f"Category : {recommendation.get('provider_category', 'unknown')}")
    print(f"Region   : {recommendation.get('region', args.region)}")
    print(f"Guardrail: {guardrail.get('status') or guardrail.get('is_valid') or 'unknown'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
