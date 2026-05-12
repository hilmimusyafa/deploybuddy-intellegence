# DeployBuddy RAG System

Dua RAG (Retrieval-Augmented Generation) system sebagai **injector** sebelum AI LLM inference,
dirancang untuk platform DeployBuddy.

---

## Arsitektur

```
User Input
    │
    ▼
┌───────────────────────────────────────┐
│  RAG SYSTEM 1: Architecture Recommender│
│                                       │
│  provider_pricing_curated.csv (650 rows)
│         ↓ TF-IDF Retrieval            │
│  Top-K chunks → inject ke System Prompt│
│         ↓ LLM Inference               │
│  Output: Arsitektur + Comparison Table│
│          + JSON Deployment Spec       │
└───────────────────────────────────────┘
    │
    │  deploy_json (JSON)
    ▼
┌───────────────────────────────────────┐
│  RAG SYSTEM 2: Deploy Code Generator  │
│                                       │
│  provider_deploy_api.csv (16 rows)    │
│         ↓ Provider Lookup / TF-IDF    │
│  API Docs → inject ke System Prompt   │
│         ↓ LLM Inference               │
│  Output: deploy.py                    │
│          .env.example                 │
│          DEPLOY_README.md             │
└───────────────────────────────────────┘
```

---

## File Structure

```
deploybuddy_rag/
├── config.py          # LLM & RAG settings (env-driven)
├── llm_client.py      # Dynamic LLM client (Ollama/OpenAI/Anthropic/Groq)
├── data_loader.py     # CSV → text chunks loader
├── rag_architecture.py # RAG System 1: TF-IDF + Architecture LLM
├── rag_deployer.py    # RAG System 2: Provider lookup + Deploy Code LLM
├── main.py            # CLI entry point
├── .env.example       # Environment variable template
├── requirements.txt
└── data/
    ├── provider_pricing_curated.csv   ← detachable, ganti sesuai kebutuhan
    └── provider_deploy_api.csv        ← detachable, ganti sesuai kebutuhan
```

---

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy dan isi .env
cp .env.example .env
# Edit .env: pilih LLM_PROVIDER dan isi API key

# 3. Taruh CSV dataset di folder data/
mkdir data
cp /path/to/provider_pricing_curated.csv data/
cp /path/to/provider_deploy_api.csv data/
```

---

## Mengganti LLM Provider

Di `.env`, ganti:

```env
# Lokal (Ollama)
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.1:8b

# OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

# Anthropic Claude
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Groq (gratis, cepat)
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...
```

Atau lewat env var langsung:
```bash
LLM_PROVIDER=groq python main.py --mode pipeline
```

---

## CLI Usage

```bash
# Full pipeline dari GitHub public repository
python main.py --mode pipeline \
  --repo-url "https://github.com/user/project.git" \
  --budget 50 \
  --ccu 500 \
  --region "Southeast Asia"

# Full pipeline dari folder lokal / upload yang sudah diekstrak
python main.py --mode pipeline \
  --repo-path "../uploads/my-app" \
  --budget 30 \
  --ccu 200 \
  --region "Indonesia"

# Full pipeline (RAG 1 → RAG 2)
python main.py --mode pipeline \
  --stack "Next.js, Golang API, PostgreSQL" \
  --budget 50 \
  --ccu 500 \
  --region "Southeast Asia" \
  --services frontend backend database

# Hanya arsitektur
python main.py --mode architecture \
  --stack "React, FastAPI, MongoDB" \
  --budget 20 --ccu 100

# Hanya arsitektur, stack otomatis dari repository
python main.py --mode architecture \
  --repo-path "../examples/next-fastapi" \
  --budget 20 \
  --ccu 100 \
  --region "Southeast Asia"

# Hanya generate kode deploy (dari provider list)
python main.py --mode deploy --providers AWS Supabase

# Dari JSON file hasil RAG 1
python main.py --mode deploy --json-file ./output/deployment_spec.json
```

### Repository Intelligence Input

Sebelum RAG 1 berjalan, DeployBuddy bisa membaca kode user lewat:

- `--repo-url`: clone GitHub public repository ke temporary directory, analisis, lalu temporary clone dibersihkan.
- `--repo-path`: baca folder lokal atau hasil upload yang sudah diekstrak.

Analyzer membaca manifest dan config penting seperti `package.json`, `requirements.txt`, `pyproject.toml`,
`go.mod`, `Dockerfile`, `docker-compose.yml`, `.env.example`, config framework, dan workflow deployment.
Folder/file berat atau sensitif seperti `.git`, `node_modules`, `venv`, `.env`, build output, binary files,
key/certificate, dan database lokal akan dilewati.

Output analyzer di-inject ke RAG 1 sebagai `REPOSITORY ANALYSIS CONTEXT`, berisi detected stack,
service types, runtime, database, dependency summary, architecture hints, important files, dan snippet
kode/config terpilih. Jika repository diberikan, stack terdeteksi menjadi sumber utama rekomendasi;
`--stack` hanya menjadi catatan tambahan/override dari user.

Untuk smoke test tanpa API key atau Ollama:

```bash
python main.py --mode architecture \
  --repo-path "../examples/next-fastapi" \
  --llm mock \
  --budget 30 \
  --ccu 200 \
  --region "Southeast Asia"
```

Catatan batasan saat ini:

- Private GitHub repository belum memakai GitHub Apps/fine-grained installation token.
- Untuk private repo, clone atau upload dulu ke folder lokal lalu gunakan `--repo-path`.
- Analyzer belum menjalankan dependency install/build; ia membaca source tree secara statis agar cepat dan aman untuk hackathon.

---

## Integrasi ke Backend API

```python
from rag_architecture import ArchitectureRAG
from rag_deployer import DeployCodeRAG

# RAG 1
arch_rag = ArchitectureRAG()
arch_result = arch_rag.recommend(
    stack="Next.js, Golang, PostgreSQL",
    budget_usd=50,
    concurrent_users=500,
    target_region="Southeast Asia",
    service_types=["frontend", "backend", "database"],
)

# Ambil teks dan JSON
print(arch_result.text)         # Full recommendation text
print(arch_result.deploy_json)  # JSON deployment spec

# RAG 2 (dari hasil RAG 1)
deploy_rag = DeployCodeRAG()
deploy_result = deploy_rag.generate_from_arch_result(arch_result)

# Simpan file
deploy_result.save_files("./output")
# Menghasilkan: deploy.py, .env.example, DEPLOY_README.md
```

---

## Mengganti Dataset CSV (Detachable)

Dataset CSV bisa diganti kapan saja tanpa ubah kode:

```env
# Di .env
PRICING_CSV_PATH=data/my_custom_pricing.csv
DEPLOY_API_CSV_PATH=data/my_custom_deploy_api.csv
```

Format CSV harus mengikuti schema yang sama:
- `provider_pricing_curated.csv`: kolom provider, category, product, service_type, region_code, region_name, sku_or_plan, cpu_vcpu, memory_gb, storage_gb, gpu, price_amount, price_unit, currency, billing_basis, notes, source_url, fetched_at
- `provider_deploy_api.csv`: kolom provider, category, deploy_target, api_type, auth_method, required_secret_names, minimum_permissions, create_endpoint_or_sdk, deploy_flow, rollback_or_delete_flow, docs_url, notes

---

## How RAG Works (Technical)

### RAG System 1 — TF-IDF Retrieval
1. Semua 650 baris CSV di-convert jadi text chunks saat startup
2. TF-IDF matrix dibangun dengan `ngram_range=(1,2)` dan `sublinear_tf=True`
3. Query dibentuk dari: `{stack} {service_types} {region} {budget} {ccu}`
4. Cosine similarity → top-K chunks
5. Chunks di-inject ke system prompt sebagai "PROVIDER KNOWLEDGE BASE"
6. LLM menerima: System Prompt (instructions + knowledge) + User Message (requirements)
7. Output diparse untuk mengekstrak JSON deployment spec

### RAG System 2 — Provider Lookup + TF-IDF Fallback
1. 16 baris deploy API CSV di-load ke dict `{provider_name: chunk}`
2. Provider names dari JSON RAG 1 di-lookup secara exact match
3. Jika tidak ada → TF-IDF cosine similarity fallback
4. API docs di-inject ke prompt sebagai "PROVIDER DEPLOY API DOCUMENTATION"
5. LLM generate `deploy.py`, `.env.example`, `DEPLOY_README.md`
