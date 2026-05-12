import os
import json
import argparse

from llm_client import get_llm_client_from_env
from rag_1 import ArchitectureRAG
from rag_2 import DeploymentCodeRAG
from stores import collection_pricing, collection_deploy
from repository_analyzer import analyze_repository, RepositoryAnalysisError

def main():
    parser = argparse.ArgumentParser(description="DeployBuddy Full Pipeline (RAG 1 & RAG 2)")
    parser.add_argument("--repo-url", type=str, default="", help="URL GitHub Repository (Kosongkan jika ingin pakai repo-path)")
    parser.add_argument("--repo-path", type=str, default="", help="Path direktori kode lokal (Jika repo-url tidak diisi)")
    parser.add_argument("--max-snippets", type=int, default=2, help="Batas maksimal code snippet")
    parser.add_argument("--budget", type=int, default=30, help="Budget target USD")
    args = parser.parse_args()

    # Pastikan minimal salah satu input kode diberikan
    repo_url = args.repo_url if args.repo_url else None
    repo_path = args.repo_path if not repo_url and args.repo_path else None

    if not repo_url and not repo_path:
        repo_url = "https://github.com/segmenta-organize/golang-backend" # Default fallback

    print(f"\n[STEP 0] Menganalisis repository: {repo_url or repo_path} ...")
    try:
        profile = analyze_repository(
            repo_url=repo_url,
            repo_path=repo_path,
            max_files=15,
            max_snippets=args.max_snippets
        )
        profile.print_summary()
    except RepositoryAnalysisError as e:
        print(f"Error analyzing repo/path: {e}")
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
        "sample_code_snippets": snippets_data
    }

    user_prefs = {
        "budget_monthly_usd": args.budget,
        "target_ccu": 200,
        "target_regions": ["Asia Tenggara", "Indonesia"],
        "service_type": "web_application"
    }

    # --- Setup LLM & RAG (Dynamic Env) ---
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        backend, llm = get_llm_client_from_env()
    except Exception as e:
        print(f"\n[ERROR] Gagal menginisialisasi LLM: {e}")
        print("[INFO] Isi API key di .env atau jalankan: $env:LLM_BACKEND='mock'")
        return

    rag1 = ArchitectureRAG(collection_pricing, collection_deploy, llm)
    rag2 = DeploymentCodeRAG(collection_deploy, llm)

    print("\n[STEP 1] Meminta rekomendasi arsitektur ke AI (RAG-1)...")
    try:
        plan = rag1.recommend(tech_stack, user_prefs)
    except Exception as e:
        print(f"\n[ERROR] Gagal memanggil LLM backend '{backend}' di RAG-1: {e}")
        print("[INFO] Periksa API key, model/limit token, atau gunakan LLM_BACKEND=mock untuk test offline.")
        return

    print("\n=== Hasil Rekomendasi Arsitektur ===")
    print(json.dumps(plan, indent=2, ensure_ascii=False))

    # --- Eksekusi RAG 2 ---
    if "provider" in plan and "deployment_plan" in plan:
        provider = plan["provider"]
        deployment_plan = plan["deployment_plan"]
        
        print(f"\n[STEP 2] Meminta pembuatan kode deploy (RAG-2) untuk provider {provider}...")
        try:
            deploy_code = rag2.generate_code(deployment_plan, provider)
        except Exception as e:
            print(f"\n[ERROR] Gagal memanggil LLM backend '{backend}' di RAG-2: {e}")
            print("[INFO] Periksa API key, model/limit token, atau gunakan LLM_BACKEND=mock untuk test offline.")
            return
        
        print("\n=== Draft Deployment Package ===")
        print(deploy_code)

        # Output kode opsional bisa disimpan ke file
        with open("deployment_package.md", "w", encoding="utf-8") as f:
            f.write(deploy_code)
            print("\n[INFO] Draft deployment package berhasil disimpan di 'deployment_package.md'.")
    else:
        print("\n[INFO] Tidak dapat melanjutkan ke RAG-2 karena RAG-1 tidak menghasilkan list 'provider' atau 'deployment_plan' yang valid.")

if __name__ == "__main__":
    main()
