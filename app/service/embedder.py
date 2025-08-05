from sentence_transformers import SentenceTransformer
import json
import os

# Load the BGE model
model = SentenceTransformer("BAAI/bge-base-en-v1.5")

def embed_chunks(json_path, source_file="unknown"):
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"{json_path} not found")

    # Load the chunked file
    with open(json_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)  # List of strings

    texts = [f"passage: {text}" for text in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)

    # Qdrant-compatible structure
    points = [
        {
            "id": i,
            "vector": emb.tolist(),
            "payload": {
                "text": text,
                "source_file": source_file,
                "chunk_index": i
            }
        }
        for i, (text, emb) in enumerate(zip(texts, embeddings))
    ]

    # Save to file
    out_path = json_path.replace(".json", "_qdrant_ready.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(points, f, ensure_ascii=False, indent=2)

    print(f"✅ Qdrant-ready file saved to {out_path}")
    return out_path
