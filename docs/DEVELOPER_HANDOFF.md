# DeployBuddy Developer Handoff

Dokumen ini dibuat untuk membantu developer manusia atau AI agent berikutnya melanjutkan DeployBuddy dari kondisi repository saat ini. Fokusnya adalah memahami sistem, menjalankan MVP, mengintegrasikan website, dan meneruskan pekerjaan auto-deploy secara aman.

## 1. Ringkasan Produk

DeployBuddy adalah AI deployment assistant. User memberikan repository aplikasi dan kebutuhan bisnis seperti budget, target concurrent users, region, dan jenis service. Sistem menganalisis code, memilih provider deployment yang masuk akal, membuat estimasi resource/biaya, lalu menghasilkan paket deployment seperti Dockerfile, docker-compose, GitHub Actions, `.env.example`, dan guide.

Target PRD utama:

- Repository & Architecture Intelligence.
- FinOps & Cost Predictability.
- Deployment Generation.
- Interactive Deployment.
- Auto-deploy di tahap lanjutan dengan secret management yang aman.

Status saat ini: core backend MVP sudah berjalan via CLI. Website/API wrapper dan auto-deploy orchestrator belum dibuat.

## 2. Kondisi Implementasi Saat Ini

Yang sudah tersedia:

- `repository_analyzer.py`
  - Membaca repository lokal atau GitHub publik.
  - Mendeteksi runtime, framework, database, package manager, service type, Docker, RAG/vector search, dan LLM integration.
  - Mengambil snippet aman dari file penting.
  - Melewati `.env`, private key, database lokal, `node_modules`, `.git`, dan folder besar lain.
  - Membaca nama env var dari `.env.example` tanpa membaca value secret dari `.env`.

- `stores.py`
  - Membaca `provider_pricing_curated.csv` dan `provider_deploy_api.csv`.
  - Membuat collection ChromaDB:
    - `provider_pricing`
    - `provider_deploy_api`
  - Menggunakan SentenceTransformer embedding.

- `rag_1.py`
  - RAG rekomendasi arsitektur/provider.
  - Menghasilkan JSON dengan provider, provider category, resource estimate, cost estimate, comparison matrix, guide, risk notes, dan deployment plan.
  - Punya guardrail anti-halusinasi:
    - Supabase/Neon/Firebase/MongoDB tidak boleh menjadi backend compute utama.
    - Provider database/BaaS hanya boleh menjadi supporting service kecuali workload memang database.
    - Provider utama harus berasal dari kategori yang eligible untuk workload.

- `rag_2.py`
  - RAG deployment package generator.
  - Menghasilkan Markdown berisi draft Dockerfile, docker-compose, GitHub Actions, `.env.example`, optional deploy script, guide, dan verify commands.
  - Jika data API provider kurang, output harus memakai `TODO`, bukan mengarang endpoint atau secret.

- `llm_client.py`
  - Abstraksi LLM backend.
  - Mendukung `groq`, `google`, `openai`, `ollama`, `local`, dan `mock`.
  - `mock` dipakai untuk offline test yang deterministik.

- `deploybuddy.py`
  - CLI MVP utama.
  - Flow:
    1. repository analyzer
    2. RAG-1 recommendation
    3. RAG-2 deployment package
  - Output:
    - `repository_profile.json`
    - `recommendation.json`
    - `deployment_package.md`

- `api.py`
  - FastAPI wrapper untuk integrasi website.
  - Mengikuti pola endpoint dari `polaBE.md`: conversation, token, dan `POST /deploy`.
  - Token disimpan in-memory untuk MVP dan value selalu dimasking saat response.
  - `POST /deploy` menjalankan pipeline analyzer -> RAG-1 -> RAG-2 dan mengembalikan raw output plus `ui_recommendation` untuk frontend.

Yang belum tersedia:

- API backend untuk website.
- Frontend web UI.
- Deployment job orchestration.
- Provider deploy adapter.
- Secret management production.
- Auto-deploy real ke cloud provider.

## 3. Struktur File Penting

```text
.
|-- api.py                        # FastAPI backend wrapper untuk website
|-- deploybuddy.py                # CLI MVP utama
|-- repository_analyzer.py        # Deteksi repo dan snippet aman
|-- rag_1.py                      # RAG rekomendasi arsitektur
|-- rag_2.py                      # RAG deployment package generator
|-- stores.py                     # Loader dataset dan ChromaDB
|-- llm_client.py                 # Abstraksi backend LLM
|-- provider_pricing_curated.csv  # Dataset pricing provider
|-- provider_deploy_api.csv       # Dataset deployment API/provider
|-- requirements.txt              # Dependency runtime
|-- tests/                        # Unit test analyzer
|-- README.md                     # Dokumentasi singkat penggunaan
`-- docs/DEVELOPER_HANDOFF.md     # Dokumen handoff ini
```

## 4. Setup Dari Awal

Jalankan dari root repository:

```powershell
python -c "import sys; print(sys.executable); print(sys.version)"
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

Catatan environment:

- Jangan memakai env `deeplearning`.
- Jangan membuat venv baru jika mengikuti setup saat ini.
- Python aktif yang pernah dipakai: `C:\ProgramData\miniconda3\python.exe`.
- Jika package masuk ke user site karena base Miniconda tidak writable, itu masih bisa dipakai selama interpreter yang sama aktif.

Copy template env:

```powershell
Copy-Item .env.example .env
```

Pilih salah satu backend:

```env
LLM_PROVIDER=mock
```

atau live Groq:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

Jangan commit `.env`.

## 5. Cara Menjalankan MVP CLI

Offline deterministic:

```powershell
$env:LLM_PROVIDER="mock"
$env:LLM_BACKEND="mock"
python deploybuddy.py --repo-path "." --budget 30 --ccu 200 --region "Indonesia" --output output
```

Live dengan `.env`:

```powershell
python deploybuddy.py --repo-path "." --budget 30 --ccu 200 --region "Indonesia" --output output
```

Input GitHub publik:

```powershell
python deploybuddy.py --repo-url "https://github.com/user/repo" --budget 30 --ccu 200 --region "Indonesia" --output output
```

Output folder:

```text
output/
|-- repository_profile.json
|-- recommendation.json
`-- deployment_package.md
```

## 6. Cara Testing

Compile semua file Python:

```powershell
$files = Get-ChildItem -Filter *.py | ForEach-Object { $_.FullName }
python -m py_compile @files
```

Unit test:

```powershell
python -m unittest discover -s tests -v
```

Smoke test CLI:

```powershell
$env:LLM_PROVIDER="mock"
python deploybuddy.py --repo-path "." --budget 30 --ccu 200 --region "Indonesia" --output output
```

Expected result:

- Compile berhasil tanpa output error.
- Unit test analyzer lulus.
- CLI menghasilkan 3 file output.
- Guardrail `is_valid` bernilai `true`.
- `.env` tidak muncul di snippet atau prompt context.

## 7. Kontrak Data Utama

### Repository Profile

`repository_profile.json` minimal berisi:

```json
{
  "source": "...",
  "detected_stack": ["..."],
  "service_types": ["..."],
  "runtimes": ["..."],
  "frameworks": {},
  "databases": ["..."],
  "package_managers": ["..."],
  "important_files": ["..."],
  "dependency_summary": {},
  "env_vars_detected": ["..."],
  "architecture_hints": ["..."],
  "warnings": ["..."],
  "file_count_scanned": 0
}
```

### RAG-1 Recommendation

`recommendation.json` harus punya field:

```json
{
  "architecture_diagram": "Mermaid diagram",
  "detected_repository_profile": {},
  "provider": "selected primary provider",
  "provider_category": "web_instant|backend|cloud_major|database|ml_best",
  "service_model": "Container/Serverless/etc",
  "region": "recommended region",
  "resource_spec": {},
  "estimated_monthly_cost_usd": 0,
  "provider_comparison_matrix": [],
  "supporting_services": [],
  "guide": "markdown guide",
  "deployment_plan": {},
  "risk_notes": "limitations and assumptions",
  "confidence": "high|medium|low",
  "guardrail": {
    "is_valid": true,
    "reason": "...",
    "provider": "...",
    "provider_category": "...",
    "primary_workload": "..."
  }
}
```

### RAG-2 Deployment Package

`deployment_package.md` harus berisi bagian:

- Summary.
- Dockerfile.
- docker-compose.
- GitHub Actions.
- `.env.example`.
- Optional provider deploy script marked as draft.
- Provider guide.
- Verify commands.
- Risk notes/TODO jika data provider belum cukup.

## 8. Integrasi Website

Core logic sudah siap dipanggil website, tetapi perlu API wrapper. Rekomendasi langkah:

### 8.1 Backend API

`api.py` sudah tersedia sebagai wrapper awal. Jalankan:

```powershell
python -m uvicorn api:app --host 127.0.0.1 --port 8000 --reload
```

Endpoint minimal:

```text
POST /analyze
```

Catatan: implementasi saat ini memakai `POST /deploy` sesuai `polaBE.md`. Jika frontend lama masih mencari `/analyze`, buat alias route yang memanggil handler `/deploy` yang sama.

Request:

```json
{
  "repo_url": "https://github.com/user/repo",
  "repo_path": null,
  "budget": 30,
  "ccu": 200,
  "region": "Indonesia",
  "service_type": "auto",
  "max_snippets": 2
}
```

Response:

```json
{
  "repository_profile": {},
  "recommendation": {},
  "deployment_package": "markdown text"
}
```

Implementation note:

- Jangan panggil CLI via shell kalau bisa import function langsung.
- Refactor reusable function dari `deploybuddy.py`, misalnya `run_pipeline(args)`, agar CLI dan API memakai logic yang sama.
- Jangan kirim `.env` value ke frontend.

### 8.2 Frontend UI

Halaman MVP:

- Form:
  - Repo URL atau upload/path mode.
  - Budget USD.
  - CCU.
  - Region.
  - Service type.
- Loading state:
  - Analyzing repository.
  - Retrieving provider data.
  - Generating recommendation.
  - Generating deployment package.
- Result:
  - Detected stack.
  - Provider utama.
  - Provider comparison matrix.
  - Region/resource/cost.
  - Architecture diagram.
  - Risk notes.
  - Markdown deployment package.

Jangan tampilkan secret value. Hanya tampilkan nama env var.

## 9. Rencana Auto-Deploy Yang Aman

Auto-deploy belum boleh langsung menjalankan script dari LLM. RAG-2 hanya boleh membuat draft. Eksekusi harus lewat orchestrator deterministic.

### 9.1 Prinsip Keamanan

- LLM tidak boleh menerima secret value.
- LLM tidak boleh menentukan command arbitrary yang langsung dieksekusi.
- User harus approve sebelum deploy.
- Semua provider integration harus lewat adapter typed/deterministic.
- Simpan log job, status, error, dan deployment URL.
- Mulai dari dry-run sebelum real deploy.

### 9.2 Struktur Modul Yang Disarankan

```text
deployment/
|-- orchestrator.py
|-- jobs.py
|-- validators.py
|-- secrets.py
`-- providers/
    |-- base.py
    |-- vercel.py
    |-- railway.py
    |-- render.py
    |-- flyio.py
    `-- local_docker.py
```

### 9.3 Job State Machine

```text
created
-> waiting_for_user_approval
-> validating_credentials
-> preparing_artifacts
-> building
-> deploying
-> verifying
-> success
```

Failure states:

```text
failed_validation
failed_build
failed_deploy
failed_verify
cancelled
```

### 9.4 Provider Adapter Interface

Setiap provider adapter sebaiknya punya interface:

```python
class DeployProvider:
    provider_name: str

    def validate_credentials(self, secrets: dict) -> None:
        ...

    def validate_plan(self, deployment_plan: dict) -> None:
        ...

    def prepare_artifacts(self, repo_path: str, deployment_plan: dict) -> list[str]:
        ...

    def deploy(self, repo_path: str, deployment_plan: dict, secrets: dict) -> dict:
        ...

    def get_logs(self, deployment_id: str) -> str:
        ...

    def verify(self, deployment_result: dict) -> dict:
        ...
```

### 9.5 Endpoint Auto-Deploy

Tambahkan setelah `/analyze` stabil:

```text
POST /deploy/preview
POST /deploy/approve
GET  /deploy/jobs/{job_id}
GET  /deploy/jobs/{job_id}/logs
POST /deploy/jobs/{job_id}/cancel
```

`/deploy/preview`:

- Menerima `recommendation`, `deployment_package`, dan provider target.
- Menghasilkan daftar action tanpa eksekusi:
  - provider yang dipakai
  - env var yang dibutuhkan
  - file yang akan dibuat
  - command/API call high-level
  - risiko

`/deploy/approve`:

- Hanya menerima job yang sudah preview.
- Memvalidasi secret tersedia.
- Menjalankan adapter provider.

### 9.6 Provider Pertama Yang Direkomendasikan

Pilih satu provider dulu agar scope kecil:

- Vercel untuk frontend/static/Next.js.
- Render atau Railway untuk backend container.
- Local Docker untuk demonstrasi tanpa cloud.

Untuk MVP tercepat, mulai dari `local_docker` dry-run:

- Validasi ada Dockerfile atau generate draft.
- Jalankan build hanya jika user approve.
- Healthcheck ke localhost.

Lalu lanjut Vercel:

- Butuh `VERCEL_TOKEN`.
- Butuh project/team/org config.
- Secret disimpan server-side.
- Deploy via Vercel API/CLI adapter, bukan command bebas dari LLM.

## 10. Guardrail Anti-Halusinasi

Jangan menghapus guardrail di `rag_1.py`. Ini bagian penting produk.

Aturan penting:

- Backend/API/worker harus memakai compute/hosting provider sebagai primary.
- Supabase/Neon/Firebase/MongoDB hanya supporting service untuk backend, bukan backend compute utama.
- Jika data provider tidak ada di dataset, RAG harus bilang data tidak cukup.
- Jika LLM memilih provider yang tidak eligible, output harus direpair atau ditolak.
- Region yang tidak masuk akal harus dinormalisasi ke preferensi user.

Jika menambah provider baru:

1. Tambahkan row di `provider_deploy_api.csv`.
2. Tambahkan pricing di `provider_pricing_curated.csv`.
3. Pastikan `category` sesuai:
   - `web_instant`
   - `backend`
   - `cloud_major`
   - `database`
   - `ml_best`
4. Jalankan ulang smoke test.

## 11. Secret Management

Saat ini MVP memakai `.env` lokal. Untuk production:

- Jangan simpan secret plain text.
- Gunakan encrypted DB field, KMS, Vault, atau secret manager provider.
- LLM hanya boleh menerima nama env var, misalnya `GROQ_API_KEY`, bukan valuenya.
- Frontend tidak boleh menerima secret value dari backend.
- Deployment logs harus dimasking.

Minimal masking:

```text
sk-1234567890abcdef -> sk-************
ghp_xxxxxxxxxxxxxxx -> ghp_************
```

## 12. Prioritas Pekerjaan Berikutnya

Urutan yang paling aman:

1. Refactor `deploybuddy.py` agar pipeline bisa dipanggil sebagai function.
2. Buat `api.py` dengan endpoint `POST /analyze`.
3. Sambungkan website ke `/analyze`.
4. Buat UI result untuk recommendation dan deployment package.
5. Tambahkan `/deploy/preview` dry-run.
6. Tambahkan `deployment/providers/local_docker.py`.
7. Tambahkan job store sederhana, misalnya JSON/SQLite.
8. Tambahkan provider cloud pertama: Vercel atau Render.
9. Tambahkan secret encryption/masking.
10. Baru pertimbangkan real auto-deploy multi-provider.

## 13. Acceptance Criteria Untuk Integrasi Website

Website dianggap MVP-ready jika:

- User bisa input repo URL, budget, CCU, region, service type.
- Backend mengembalikan repository profile.
- Backend mengembalikan recommendation valid.
- Backend mengembalikan deployment package markdown.
- UI menampilkan detected stack, provider, cost, comparison matrix, guide, risk notes.
- `.env` tidak pernah muncul di UI atau response.
- Jika LLM/API error, UI menampilkan pesan actionable.
- Mode `mock` bisa dipakai untuk demo offline.

## 14. Acceptance Criteria Untuk Auto-Deploy

Auto-deploy dianggap aman untuk MVP jika:

- Ada preview sebelum deploy.
- Ada approval eksplisit dari user.
- Secret tidak dikirim ke LLM.
- Provider adapter deterministic.
- Tidak menjalankan arbitrary shell command dari output LLM.
- Ada job status dan log.
- Ada healthcheck/verify step.
- Ada rollback/cancel minimal atau instruksi manual rollback.

## 15. Catatan Untuk AI Agent Berikutnya

Jika melanjutkan pekerjaan:

- Baca README dan dokumen ini dulu.
- Jangan print isi `.env`.
- Jangan menghapus guardrail anti-halusinasi.
- Jangan reset `chroma_db/` kecuali user meminta.
- Jangan masuk env `deeplearning`.
- Pakai `LLM_PROVIDER=mock` untuk test cepat.
- Setelah edit Python, jalankan:

```powershell
$files = Get-ChildItem -Filter *.py | ForEach-Object { $_.FullName }
python -m py_compile @files
python -m unittest discover -s tests -v
```

- Untuk website/API, buat perubahan kecil bertahap dan jaga agar CLI tetap berjalan.

## 16. Known Issues Dan Risiko

- `chroma_db/` dan `__pycache__/` masih terlihat dalam repo state. Idealnya masuk `.gitignore`, tetapi jangan ubah tanpa koordinasi jika sudah tracked.
- `stores.py` membangun/meng-upsert Chroma saat import. Untuk API production, pertimbangkan lazy singleton agar startup lebih terkendali.
- Live LLM bisa menghasilkan output bervariasi. Gunakan normalizer dan guardrail sebelum output dipakai.
- Auto-deploy penuh butuh keputusan provider, secret storage, job queue, dan approval UX.
- Dataset pricing masih curated/sintetis, belum real-time API resmi.

## 17. Definition Of Done Akhir Produk

DeployBuddy mendekati visi PRD jika:

- Bisa membaca repository user.
- Bisa mengunci stack yang terdeteksi agar rekomendasi tidak halu.
- Bisa memberi provider recommendation dengan comparison matrix dan cost estimate.
- Bisa membuat deployment package yang dapat direview.
- Bisa mengintegrasikan website dengan pipeline backend.
- Bisa melakukan deploy preview dan approval.
- Bisa menjalankan deploy provider tertentu lewat adapter aman.
- Bisa menyimpan job history dan logs.
- Bisa mengelola secret tanpa membocorkan value ke LLM, frontend, atau logs.
