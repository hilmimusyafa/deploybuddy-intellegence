import pandas as pd
import chromadb
from chromadb.utils import embedding_functions

# ==================== LOAD CSV ====================
df_pricing = pd.read_csv("provider_pricing_curated.csv")
df_deploy  = pd.read_csv("provider_deploy_api.csv")

# Buat dokumen teks dari tiap baris
def pricing_row_to_doc(row):
    return (
        f"Provider: {row['provider']}, Category: {row['category']}, Service: {row['product']}, "
        f"Type: {row['service_type']}, Region: {row['region_name']} ({row['region_code']}), "
        f"SKU/Plan: {row['sku_or_plan']}, vCPU: {row['cpu_vcpu']}, RAM: {row['memory_gb']}GB, "
        f"Storage: {row['storage_gb']}GB, GPU: {row['gpu']}, Price: {row['price_amount']} {row['price_unit']} "
        f"in {row['currency']}, Billing: {row['billing_basis']}, Notes: {row['notes']}, "
        f"Source: {row['source_url']}"
    )

def deploy_row_to_doc(row):
    return (
        f"Provider: {row['provider']}, Category: {row['category']}, Target: {row['deploy_target']}, "
        f"API Type: {row['api_type']}, Auth: {row['auth_method']}, Secrets: {row['required_secret_names']}, "
        f"Permissions: {row['minimum_permissions']}, Endpoint/SDK: {row['create_endpoint_or_sdk']}, "
        f"Deploy Flow: {row['deploy_flow']}, Rollback/Delete: {row['rollback_or_delete_flow']}, "
        f"Docs: {row['docs_url']}, Notes: {row['notes']}"
    )

docs_pricing = [pricing_row_to_doc(row) for _, row in df_pricing.iterrows()]
docs_deploy  = [deploy_row_to_doc(row) for _, row in df_deploy.iterrows()]

# ==================== SETUP VECTOR STORE ====================
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

client = chromadb.PersistentClient(path="./chroma_db")

# Koleksi terpisah untuk pricing dan deploy
collection_pricing = client.get_or_create_collection(
    name="provider_pricing",
    embedding_function=sentence_transformer_ef
)
collection_deploy = client.get_or_create_collection(
    name="provider_deploy_api",
    embedding_function=sentence_transformer_ef
)

# Isi data (lakukan hanya sekali, bisa ditambahkan pengecekan agar tidak duplikat)
batch_size = 200
for i in range(0, len(docs_pricing), batch_size):
    batch = docs_pricing[i:i+batch_size]
    collection_pricing.add(
        documents=batch,
        ids=[str(j) for j in range(i, i+len(batch))]
    )

for i in range(0, len(docs_deploy), batch_size):
    batch = docs_deploy[i:i+batch_size]
    collection_deploy.add(
        documents=batch,
        ids=[f"d{j}" for j in range(i, i+len(batch))]
    )

print("Vector stores ready.")