# app/utils/embedder.py

import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np

def embed_chunks(json_path: str):
    # Load chunks
    with open(json_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    # Load embedding model
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Generate embeddings
    embeddings = model.encode(chunks, show_progress_bar=True)

    # Save embeddings (optional)
    embeddings_path = Path(json_path).with_name("chunked_embeddings.npy")
    np.save(embeddings_path, embeddings)

    print(f"Embedded {len(chunks)} chunks.")
    print(f"Embeddings saved at: {embeddings_path}")

    return embeddings_path