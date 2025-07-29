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

# ------------------ LLM (Groq) ------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")  # Required for Groq
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_TEMPERATURE = 0.1  # Lower temperature for more factual responses
GROQ_MAX_TOKENS = 1024  # Maximum tokens for response

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
ENABLE_AUTH = True  # Enable authentication
API_KEY_HEADER = "X-API-Key"
# Default token if none provided in environment
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "a692774361df87466df8df0cbdecb1a9daca509b1a31d0948aad64b7b3ae5f12")

# ------------------ Logging ------------------
ENABLE_LOGGING = True
LOG_LEVEL = "INFO"
