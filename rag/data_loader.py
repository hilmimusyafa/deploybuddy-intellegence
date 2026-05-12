"""
DeployBuddy RAG — Data Loader
================================
Membaca CSV dan mengubah setiap baris menjadi "chunk teks" yang
bisa di-index oleh TF-IDF / vector store.

CSV bersifat detachable: path dikontrol dari config.py atau env var.
"""

import csv
from typing import List, Dict


# ─────────────────────────────────────────────────────────────────────────────
# LOADER 1 — Provider Pricing CSV  →  RAG System 1
# ─────────────────────────────────────────────────────────────────────────────

def load_pricing_chunks(csv_path: str) -> List[Dict]:
    """
    Baca provider_pricing_curated.csv.
    Setiap baris → satu "chunk" berisi teks natural + metadata asli.

    Return:
        List of {
            "text": str,         # teks untuk di-index (query similarity)
            "metadata": dict,    # baris CSV asli (untuk ditampilkan ke LLM)
        }
    """
    chunks = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Buat teks natural language dari kolom CSV
            price_info = (
                f"${row['price_amount']}/{row['price_unit']}"
                if row["price_amount"]
                else f"price varies (see docs)"
            )
            text = (
                f"Provider: {row['provider']} | "
                f"Category: {row['category']} | "
                f"Product: {row['product']} | "
                f"Service type: {row['service_type']} | "
                f"Region: {row['region_name']} ({row['region_code']}) | "
                f"Plan/SKU: {row['sku_or_plan']} | "
                f"CPU: {row['cpu_vcpu']} vCPU | "
                f"Memory: {row['memory_gb']} GB | "
                f"Storage: {row['storage_gb']} GB | "
                f"GPU: {row['gpu']} | "
                f"Price: {price_info} {row['currency']} | "
                f"Billing: {row['billing_basis']} | "
                f"Notes: {row['notes']}"
            )
            chunks.append({"text": text, "metadata": dict(row)})
    return chunks


def pricing_chunk_to_context(chunk: Dict) -> str:
    """Format satu chunk pricing menjadi teks ringkas untuk dimasukkan ke prompt."""
    m = chunk["metadata"]
    price = f"${m['price_amount']}/{m['price_unit']}" if m["price_amount"] else "price via API"
    return (
        f"• [{m['provider']}] {m['product']} ({m['service_type']}) "
        f"| Region: {m['region_name']} "
        f"| Plan: {m['sku_or_plan']} "
        f"| {m['cpu_vcpu']} vCPU / {m['memory_gb']}GB RAM "
        f"| Price: {price} {m['currency']} ({m['billing_basis']})"
        f"| Notes: {m['notes'][:120]}..."
    )


# ─────────────────────────────────────────────────────────────────────────────
# LOADER 2 — Provider Deploy API CSV  →  RAG System 2
# ─────────────────────────────────────────────────────────────────────────────

def load_deploy_api_chunks(csv_path: str) -> List[Dict]:
    """
    Baca provider_deploy_api.csv.
    Setiap baris → satu "chunk" (per provider) berisi semua info deploy API.

    Return:
        List of {
            "text": str,
            "metadata": dict,
        }
    """
    chunks = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = (
                f"Provider: {row['provider']} | "
                f"Category: {row['category']} | "
                f"Deploy target: {row['deploy_target']} | "
                f"API type: {row['api_type']} | "
                f"Auth method: {row['auth_method']} | "
                f"Required secrets: {row['required_secret_names']} | "
                f"Minimum permissions: {row['minimum_permissions']} | "
                f"Create endpoint or SDK: {row['create_endpoint_or_sdk']} | "
                f"Deploy flow: {row['deploy_flow']} | "
                f"Rollback or delete flow: {row['rollback_or_delete_flow']} | "
                f"Docs: {row['docs_url']} | "
                f"Notes: {row['notes']}"
            )
            chunks.append({"text": text, "metadata": dict(row)})
    return chunks


def deploy_api_chunk_to_context(chunk: Dict) -> str:
    """Format satu chunk deploy API menjadi teks detail untuk dimasukkan ke prompt."""
    m = chunk["metadata"]
    return f"""
=== {m['provider']} ({m['category']}) ===
Deploy Target   : {m['deploy_target']}
API Type        : {m['api_type']}
Auth Method     : {m['auth_method']}
Required Secrets: {m['required_secret_names']}
Min Permissions : {m['minimum_permissions']}
Create Endpoint : {m['create_endpoint_or_sdk']}
Deploy Flow     : {m['deploy_flow']}
Rollback/Delete : {m['rollback_or_delete_flow']}
Docs URL        : {m['docs_url']}
Notes           : {m['notes']}
"""
