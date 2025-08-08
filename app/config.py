# config.py
import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # Load from .env file if available

# ------------------ General ------------------
APP_NAME = "RAG system made by StrawHats"
APP_VERSION = "1.0.0"


#------------------- Llama Cloud Services ------------------
LLAMA_API_KEY = os.getenv("LLAMA_CLOUD_API", "")  # Use LLAMA_CLOUD_API in .env
LLAMA_FAST_MODE = os.getenv("LLAMA_FAST_MODE", "true").lower() == "true"
LLAMA_DISABLE_OCR = os.getenv("LLAMA_DISABLE_OCR", "true").lower() == "true"
LLAMA_DISABLE_IMG = os.getenv("LLAMA_DISABLE_IMG", "true").lower() == "true"
LLAMA_HIDE_HEADERS = os.getenv("LLAMA_HIDE_HEADERS", "true").lower() == "true"
LLAMA_HIDE_FOOTERS = os.getenv("LLAMA_HIDE_FOOTERS", "true").lower() == "true"
LLAMA_LANGUAGE = os.getenv("LLAMA_LANGUAGE", "en")


# ------------------ Qdrant Vector DB ------------------Y
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "None")  # Optional
QDRANT_COLLECTION = os.getenv("VECDB_CHUNKTABLE", "rag-collection")
VECTOR_SIZE = 768  # Matches embedding model dimension
VECTOR_DISTANCE = "COSINE"  # Options: COSINE, EUCLID, DOT

# HNSW index parameters for Qdrant (as per requirements)
INDEX_HNSW_PARAMS = json.loads(os.getenv("INDEX_HNSW_PARAMS", '{"ef_construction": 200, "M": 16}'))

# ------------------ LLM (Groq) ------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")  # Required for LLM functionality
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")  # Default model
GROQ_TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", "0.2"))  # 0.0 for deterministic responses
GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "1024"))  # Maximum response length

# ------------------ Embedding Model ------------------
EMBEDDING_MODEL_NAME = os.getenv("EMBED_MODEL", "BAAI/bge-base-en-v1.5")
EMBEDDING_SIZE = 768  # Embedding dimension for bge-base-en-v1.5

# ------------------ Chunking ------------------
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "300"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
SENTENCE_SPLITTER = os.getenv("SENTENCE_SPLITTER", "nltk")  # Options: nltk, spacy, none

# ------------------ Document Parser ------------------
PARSER = os.getenv("PARSER", "PyMuPDF")  # Using PyMuPDF by default

# ------------------ Async ------------------
ASYNC_TIMEOUT = int(os.getenv("ASYNC_TIMEOUT", "20"))  # seconds for HTTP clients

# ------------------ Limits ------------------
TOP_K_RETRIEVAL = int(os.getenv("TOP_K_RETRIEVAL", "3"))

# ------------------ Security ------------------
ENABLE_AUTH = os.getenv("ENABLE_AUTH", "True").lower() == "true"  # Enable authentication
API_KEY_HEADER = os.getenv("API_KEY_HEADER", "X-API-Key")
# Default token if none provided in environment
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "")

# ------------------ Logging ------------------
ENABLE_LOGGING = os.getenv("ENABLE_LOGGING", "True").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
