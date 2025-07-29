# config.py

import os
from dotenv import load_dotenv

load_dotenv()  # Load from .env file if available

# ------------------ General ------------------
APP_NAME = "Fast & Accurate RAG System"
APP_VERSION = "1.0.0"

# ------------------ Qdrant ------------------
QDRANT_URL = os.getenv("QDRANT_URL", "https://your-qdrant-instance.qdrant.tech")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)  # Optional
QDRANT_COLLECTION = "rag-collection"
VECTOR_SIZE = 768
VECTOR_DISTANCE = "COSINE"  # Options: COSINE, EUCLID, DOT

# ------------------ Ollama / LLM ------------------
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = "llama3"

# ------------------ Embedding Model ------------------
EMBEDDING_MODEL_NAME = "BAAI/bge-base-en-v1.5"

# ------------------ Chunking ------------------
CHUNK_SIZE = 300
CHUNK_OVERLAP = 50

# ------------------ Async ------------------
ASYNC_TIMEOUT = 20  # seconds for HTTP clients

# ------------------ Limits ------------------
TOP_K_RETRIEVAL = 3

# ------------------ Security ------------------
ENABLE_AUTH = False
API_KEY_HEADER = "X-API-Key"

# ------------------ Logging ------------------
ENABLE_LOGGING = True
LOG_LEVEL = "INFO"
