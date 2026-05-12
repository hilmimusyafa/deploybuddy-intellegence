import os
import json
import argparse

from llm_client import get_llm_client_from_env
from rag_1 import ArchitectureRAG
from stores import collection_pricing, collection_deploy
from repository_analyzer import analyze_repository, RepositoryAnalysisError

def main():
    parser = argparse.ArgumentParser(description="DeployBuddy RAG Test with Local Directory")
    parser.add_argument("--repo-path", type=str, default=".", help="Path direktori kode lokal")
    parser.add_argument("--max-snippets", type=int, default=2, help="Batas maksimal code snippet (cegah Payload Too Large)")
    parser.add_argument("--budget", type=int, default=30, help="Budget target USD")
    args = parser.parse_args()

    print(f"\n[STEP 1] Menganalisis direktori lokal: {args.repo_path} ...")
    try:
        profile = analyze_repository(
            repo_path=args.repo_path,
            max_files=15,
            max_snippets=args.max_snippets
        )
        profile.print_summary()
    except RepositoryAnalysisError as e:
        print(f"Error analyzing local path: {e}")
        return

    # --- Ekstraksi Profil Repo ke Input RAG ---
    snippets_data = []
    for s in profile.snippets:
        snippets_data.append(f"File: {s.path}\n{s.content}")

    tech_stack = {
        "language": ", ".join(profile.runtimes) if profile.runtimes else "Not detected",
        "framework": ", ".join(profile.detected_stack) if profile.detected_stack else "Not detected",
        "database": ", ".join(profile.databases) if profile.databases else "Not detected",
        "type": ", ".join(profile.service_types) if profile.service_types else "Unknown",
        "architecture_hints": profile.architecture_hints,
        "sample_code_snippets": snippets_data  # Ini akan ikut di-inject ke prompt LLM
    }

    user_prefs = {
        "budget_monthly_usd": args.budget,
        "target_ccu": 200,
        "target_regions": ["Asia", "Indonesia"],
        "service_type": "web_application"
    }

    # --- Setup LLM & RAG ---
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        backend, llm = get_llm_client_from_env()
    except Exception as e:
        print(f"\n[ERROR] Gagal menginisialisasi LLM: {e}")
        print("[INFO] Isi API key di .env atau jalankan: $env:LLM_BACKEND='mock'")
        return

    rag1 = ArchitectureRAG(collection_pricing, collection_deploy, llm)

    print("\n[STEP 2] Meminta rekomendasi arsitektur ke AI...")
    try:
        plan = rag1.recommend(tech_stack, user_prefs)
    except Exception as e:
        print(f"\n[ERROR] Gagal memanggil LLM backend '{backend}': {e}")
        print("[INFO] Periksa API key, model/limit token, atau gunakan LLM_BACKEND=mock untuk test offline.")
        return

    print("\n=== Hasil Rekomendasi Arsitektur ===")
    print(json.dumps(plan, indent=2, ensure_ascii=False))

    if "provider" in plan:
        print("\n[INFO] Kode deploy (RAG-2) dinonaktifkan sementara.")

if __name__ == "__main__":
    main()
