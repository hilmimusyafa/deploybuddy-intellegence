import sys
import os
import json
import argparse

# Tambahkan path aplikasi utama agar bisa import repository_analyzer
sys.path.append(os.path.abspath("../Refactory Hackathon x Telkom University/deploybuddy-intellegence"))

from llm_client import get_llm_client
from rag_1 import ArchitectureRAG
from stores import collection_pricing, collection_deploy
from repository_analyzer import analyze_repository, RepositoryAnalysisError

def main():
    parser = argparse.ArgumentParser(description="DeployBuddy RAG Test with GitHub URL")
    parser.add_argument("--repo-url", type=str, default="https://github.com/segmenta-organize/golang-backend", help="URL GitHub Repository")
    parser.add_argument("--max-snippets", type=int, default=2, help="Batas maksimal code snippet (cegah Payload Too Large)")
    parser.add_argument("--budget", type=int, default=30, help="Budget target USD")
    args = parser.parse_args()

    print(f"\n[STEP 1] Menganalisis repository: {args.repo_url} ...")
    try:
        profile = analyze_repository(
            repo_url=args.repo_url,
            max_files=15,
            max_snippets=args.max_snippets
        )
        profile.print_summary()
    except RepositoryAnalysisError as e:
        print(f"Error analyzing repo: {e}")
        return

    # --- Ekstraksi Profil Repo ke Input RAG ---
    snippets_data = []
    for s in profile.snippets:
        snippets_data.append(f"File: {s.file_path}\n{s.content}")

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
    
    BACKEND = os.getenv("LLM_BACKEND", "groq")

    if BACKEND == "groq":
        llm = get_llm_client("groq", api_key=os.getenv("GROQ_API_KEY"), model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"))
    elif BACKEND == "google":
        llm = get_llm_client("google", api_key=os.getenv("GOOGLE_API_KEY"), model=os.getenv("GOOGLE_MODEL", "gemini-1.5-flash"))
    elif BACKEND == "local":
        llm = get_llm_client("local", base_url=os.getenv("LOCAL_BASE_URL", "http://localhost:11434/v1"), model=os.getenv("LOCAL_MODEL", "llama3.1:8b"))
    else:
        raise ValueError("Backend tidak dikenal")

    rag1 = ArchitectureRAG(collection_pricing, collection_deploy, llm)

    print("\n[STEP 2] Meminta rekomendasi arsitektur ke AI...")
    plan = rag1.recommend(tech_stack, user_prefs)

    print("\n=== Hasil Rekomendasi Arsitektur ===")
    print(json.dumps(plan, indent=2, ensure_ascii=False))

    if "provider" in plan:
        print("\n[INFO] Kode deploy (RAG-2) dinonaktifkan sementara.")

if __name__ == "__main__":
    main()
