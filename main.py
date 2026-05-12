import os
import json
from dotenv import load_dotenv

from llm_client import get_llm_client
from rag_1 import ArchitectureRAG
from rag_2 import DeploymentCodeRAG
from stores import collection_pricing, collection_deploy

# Load environment variables dari file .env
load_dotenv()

# Membaca konfigurasi dari env
BACKEND = os.getenv("LLM_BACKEND", "groq")

# Inisialisasi LLM backend secara dinamis
if BACKEND == "groq":
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    llm = get_llm_client("groq", api_key=api_key, model=model)
elif BACKEND == "google":
    api_key = os.getenv("GOOGLE_API_KEY")
    model = os.getenv("GOOGLE_MODEL", "gemini-1.5-flash")
    llm = get_llm_client("google", api_key=api_key, model=model)
elif BACKEND == "local":
    base_url = os.getenv("LOCAL_BASE_URL", "http://localhost:11434/v1")
    model = os.getenv("LOCAL_MODEL", "llama3.1:8b")
    llm = get_llm_client("local", base_url=base_url, model=model)
else:
    raise ValueError(f"Backend LLM '{BACKEND}' tidak dikenal.")

# Inisialisasi RAG systems
rag1 = ArchitectureRAG(collection_pricing, collection_deploy, llm)
rag2 = DeploymentCodeRAG(collection_deploy, llm)

# Contoh input (dari analisis kode & user)
tech_stack = {
    "language": "Python",
    "framework": "FastAPI",
    "database": "PostgreSQL",
    "type": "backend"
}
user_prefs = {
    "budget_monthly_usd": 30,
    "target_ccu": 100,
    "target_regions": ["Asia Tenggara", "Singapore"],
    "service_type": "web_backend"
}

# Step 1: Dapatkan rekomendasi
plan = rag1.recommend(tech_stack, user_prefs)
print("=== Architecture & Plan ===")
print(json.dumps(plan, indent=2, ensure_ascii=False))

# Step 2: Jika user setuju, generate kode deploy
if "provider" in plan and "deployment_plan" in plan:
    provider = plan["provider"]
    deploy_code = rag2.generate_code(plan["deployment_plan"], provider)
    print("\n=== Generated Deploy Code ===")
    print(deploy_code)
else:
    print("\n[INFO] Tidak dapat men-generate kode karena tidak ada rekomendasi provider.")