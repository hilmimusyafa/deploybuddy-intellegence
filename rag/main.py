"""
DeployBuddy RAG — Main Entry Point
====================================
Menjalankan pipeline lengkap atau masing-masing RAG system.

USAGE:
  # Pipeline penuh (RAG 1 → RAG 2)
  python main.py --mode pipeline

  # Hanya rekomendasi arsitektur (RAG 1 saja)
  python main.py --mode architecture

  # Hanya generate kode deploy (RAG 2 saja, perlu JSON input)
  python main.py --mode deploy --providers AWS Supabase

  # Ganti LLM provider
  LLM_PROVIDER=openai python main.py --mode pipeline
  LLM_PROVIDER=anthropic python main.py --mode pipeline
  LLM_PROVIDER=groq python main.py --mode pipeline
  LLM_PROVIDER=ollama python main.py --mode pipeline
"""

import argparse
import json
import os

from rag_architecture import ArchitectureRAG
from rag_deployer     import DeployCodeRAG


def run_pipeline(args):
    """
    Full pipeline: RAG 1 → RAG 2.
    Bisa di-customize dengan argparse atau hardcode untuk testing.
    """
    print("\n🚀 DeployBuddy RAG Pipeline")
    print("─" * 50)

    # ── INPUT (bisa dari argparse / API / UI) ────────────────────────────────
    stack             = args.stack
    budget_usd        = args.budget
    concurrent_users  = args.ccu
    target_region     = args.region
    service_types     = args.services
    extra_notes       = args.notes
    output_dir        = args.output

    # ── RAG SYSTEM 1: Architecture Recommendation ────────────────────────────
    print("\n[STEP 1] Architecture & Provider Recommendation (RAG 1)")
    arch_rag    = ArchitectureRAG(llm_provider=args.llm)
    arch_result = arch_rag.recommend(
        stack=stack,
        budget_usd=budget_usd,
        concurrent_users=concurrent_users,
        target_region=target_region,
        service_types=service_types,
        extra_notes=extra_notes,
    )
    arch_result.print_summary()

    if not arch_result.deploy_json:
        print("\n[Warning] No JSON extracted from architecture response.")
        print("          RAG 2 will be skipped. Check LLM output above.")
        return arch_result, None

    # Simpan JSON ke file
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, "deployment_spec.json")
    with open(json_path, "w") as f:
        json.dump(arch_result.deploy_json, f, indent=2)
    print(f"\n[RAG-1] Deployment spec saved: {json_path}")

    # ── RAG SYSTEM 2: Deploy Code Generation ─────────────────────────────────
    print("\n[STEP 2] Deploy Code Generation (RAG 2)")
    deploy_rag    = DeployCodeRAG(llm_provider=args.llm)
    deploy_result = deploy_rag.generate_from_arch_result(arch_result)
    deploy_result.print_summary()
    deploy_result.save_files(output_dir)

    print(f"\n✅ All done! Output saved to: {output_dir}/")
    return arch_result, deploy_result


def run_architecture_only(args):
    """Hanya jalankan RAG System 1."""
    print("\n[MODE] Architecture Recommendation Only")
    arch_rag = ArchitectureRAG(llm_provider=args.llm)
    result   = arch_rag.recommend(
        stack=args.stack,
        budget_usd=args.budget,
        concurrent_users=args.ccu,
        target_region=args.region,
        service_types=args.services,
        extra_notes=args.notes,
    )
    result.print_summary()

    if result.deploy_json:
        os.makedirs(args.output, exist_ok=True)
        path = os.path.join(args.output, "deployment_spec.json")
        with open(path, "w") as f:
            json.dump(result.deploy_json, f, indent=2)
        print(f"\n[Saved] {path}")
    return result


def run_deploy_only(args):
    """Hanya jalankan RAG System 2 (dari daftar provider)."""
    print(f"\n[MODE] Deploy Code Generation Only → providers: {args.providers}")
    deploy_rag = DeployCodeRAG(llm_provider=args.llm)

    # Kalau ada JSON file, baca dari sana
    if args.json_file and os.path.exists(args.json_file):
        with open(args.json_file) as f:
            deploy_json = json.load(f)
        result = deploy_rag.generate_from_json(deploy_json)
    else:
        result = deploy_rag.generate_from_providers(args.providers)

    result.print_summary()
    result.save_files(args.output)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="DeployBuddy RAG System")

    # Mode
    p.add_argument("--mode", choices=["pipeline", "architecture", "deploy"],
                   default="pipeline", help="Which RAG system to run")

    # LLM provider override
    p.add_argument("--llm", type=str, default=None,
                   help="LLM provider: ollama|openai|anthropic|groq (default: from env LLM_PROVIDER)")

    # RAG 1 inputs
    p.add_argument("--stack", type=str,
                   default="Next.js frontend, Golang REST API backend, PostgreSQL database",
                   help="Tech stack description")
    p.add_argument("--budget", type=float, default=30.0,
                   help="Monthly budget in USD")
    p.add_argument("--ccu", type=int, default=200,
                   help="Peak concurrent users")
    p.add_argument("--region", type=str, default="Southeast Asia",
                   help="Target deployment region")
    p.add_argument("--services", type=str, nargs="+",
                   default=["frontend", "backend", "database"],
                   help="Service types (space-separated)")
    p.add_argument("--notes", type=str, default="",
                   help="Additional notes for the AI")

    # RAG 2 inputs (deploy only mode)
    p.add_argument("--providers", type=str, nargs="+",
                   default=["AWS", "Supabase"],
                   help="Provider names for deploy-only mode")
    p.add_argument("--json-file", type=str, default=None,
                   help="Path to deployment_spec.json (for deploy-only mode)")

    # Output
    p.add_argument("--output", type=str, default="./output",
                   help="Output directory for generated files")

    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.mode == "pipeline":
        run_pipeline(args)
    elif args.mode == "architecture":
        run_architecture_only(args)
    elif args.mode == "deploy":
        run_deploy_only(args)
