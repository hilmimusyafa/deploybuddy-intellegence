import json

from dotenv import load_dotenv

from llm_client import get_llm_client_from_env


def main():
    from rag_1 import ArchitectureRAG
    from rag_2 import DeploymentCodeRAG
    from stores import collection_pricing, collection_deploy

    # Load environment variables dari file .env
    load_dotenv()

    try:
        backend, llm = get_llm_client_from_env()
    except Exception as e:
        raise SystemExit(
            f"[ERROR] Gagal menginisialisasi LLM: {e}\n"
            "[INFO] Isi API key di .env atau jalankan dengan LLM_BACKEND=mock untuk test offline."
        )

    # Inisialisasi RAG systems
    rag1 = ArchitectureRAG(collection_pricing, collection_deploy, llm)
    rag2 = DeploymentCodeRAG(collection_deploy, llm)

    # Contoh input (dari analisis kode & user)
    tech_stack = {
        "language": "Python",
        "framework": "FastAPI",
        "database": "PostgreSQL",
        "type": "backend",
    }
    user_prefs = {
        "budget_monthly_usd": 30,
        "target_ccu": 100,
        "target_regions": ["Asia Tenggara", "Singapore"],
        "service_type": "web_backend",
    }

    # Step 1: Dapatkan rekomendasi
    try:
        plan = rag1.recommend(tech_stack, user_prefs)
    except Exception as e:
        raise SystemExit(
            f"[ERROR] Gagal memanggil LLM backend '{backend}' di RAG-1: {e}\n"
            "[INFO] Periksa API key, model/limit token, atau gunakan LLM_BACKEND=mock untuk test offline."
        )

    print("=== Architecture & Plan ===")
    print(json.dumps(plan, indent=2, ensure_ascii=False))

    # Step 2: Jika user setuju, generate kode deploy
    if "provider" in plan and "deployment_plan" in plan:
        provider = plan["provider"]
        try:
            deploy_code = rag2.generate_code(plan["deployment_plan"], provider)
        except Exception as e:
            raise SystemExit(
                f"[ERROR] Gagal memanggil LLM backend '{backend}' di RAG-2: {e}\n"
                "[INFO] Periksa API key, model/limit token, atau gunakan LLM_BACKEND=mock untuk test offline."
            )

        print("\n=== Draft Deployment Package ===")
        print(deploy_code)
    else:
        print("\n[INFO] Tidak dapat men-generate kode karena tidak ada rekomendasi provider.")


if __name__ == "__main__":
    main()
