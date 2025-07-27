import json
import uuid
from sentence_transformers import SentenceTransformer
from pymilvus import (
    connections, FieldSchema, CollectionSchema, DataType,
    Collection, utility
)

# ==== Config ====
JSON_PATH = "../dataset/combined_chunks.json"
COLLECTION_NAME = "rag_chunks"
DIMENSION = 384  # Embedding size for all-MiniLM-L6-v2
HOST = "localhost"
PORT = "19530"

# ==== Step 1: Connect to Milvus ====
connections.connect(alias="default", host=HOST, port=PORT)
print("✅ Connected to Milvus")

# ==== Step 2: Load Chunk Data ====
with open(JSON_PATH, 'r', encoding='utf-8') as f:
    chunk_data = json.load(f)

print(f"📄 Loaded {len(chunk_data)} chunks from JSON")

# ==== Step 3: Load Embedding Model ====
model = SentenceTransformer('all-MiniLM-L6-v2')
print("✅ Loaded embedding model")

# ==== Step 4: Prepare Collection ====
if utility.has_collection(COLLECTION_NAME):
    print(f"⚠️ Dropping existing collection '{COLLECTION_NAME}'...")
    Collection(COLLECTION_NAME).drop()

fields = [
    FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, auto_id=False, max_length=36),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=DIMENSION),
    FieldSchema(name="document", dtype=DataType.VARCHAR, max_length=512),
    FieldSchema(name="section", dtype=DataType.VARCHAR, max_length=512),
    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=16384),  # supports large chunk text
]

schema = CollectionSchema(fields, description="RAG chunks with embeddings")
collection = Collection(name=COLLECTION_NAME, schema=schema)
print(f"✅ Created collection '{COLLECTION_NAME}'")

# ==== Step 5: Embed & Insert Chunks ====
ids = []
embeddings = []
documents = []
sections = []
texts = []

for chunk in chunk_data:
    ids.append(str(uuid.uuid4()))
    documents.append(chunk.get("document", ""))
    sections.append(chunk.get("section", ""))
    texts.append(chunk["text"])

# Batch embed
embeddings = model.encode(texts).tolist()

collection.insert([ids, embeddings, documents, sections, texts])
print(f"✅ Inserted {len(ids)} embeddings")
collection.flush()

# ==== Step 6: Index & Load ====
collection.create_index(
    field_name="embedding",
    index_params={"index_type": "IVF_FLAT", "metric_type": "L2", "params": {"nlist": 128}}
)
collection.load()
print("✅ Index created and collection loaded for search")