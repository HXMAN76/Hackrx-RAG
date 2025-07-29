import logging
from functools import lru_cache
from typing import List, Union

from sentence_transformers import SentenceTransformer

from app.config import EMBEDDING_MODEL_NAME
from app.models import Chunk, EmbeddedChunk

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """
    Initialize and cache the embedding model.
    
    Returns:
        SentenceTransformer model
    """
    logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
    try:
        model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        logger.info(f"Successfully loaded embedding model: {EMBEDDING_MODEL_NAME}")
        return model
    except Exception as e:
        logger.error(f"Failed to load embedding model: {str(e)}")
        raise


async def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts asynchronously.
    
    Args:
        texts: List of text strings to embed
        
    Returns:
        List of embedding vectors
    """
    if not texts:
        return []
    
    try:
        model = get_embedding_model()
        # Sentence Transformers encode method is CPU-bound but optimized
        # We run it in the default ThreadPoolExecutor of asyncio
        embeddings = model.encode(texts)
        
        # Convert numpy arrays to lists for JSON serialization
        return embeddings.tolist()
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        raise


async def embed_chunks(chunks: List[Chunk]) -> List[EmbeddedChunk]:
    """
    Generate embeddings for a list of chunks.
    
    Args:
        chunks: List of Chunk objects to embed
        
    Returns:
        List of EmbeddedChunk objects with embeddings
    """
    if not chunks:
        return []
    
    try:
        # Extract texts from chunks
        texts = [chunk.text for chunk in chunks]
        
        # Generate embeddings
        embeddings = await generate_embeddings(texts)
        
        # Combine chunks with their embeddings
        embedded_chunks = []
        for chunk, embedding in zip(chunks, embeddings):
            embedded_chunks.append(
                EmbeddedChunk(
                    text=chunk.text,
                    metadata=chunk.metadata,
                    embedding=embedding
                )
            )
        
        logger.info(f"Generated embeddings for {len(embedded_chunks)} chunks")
        return embedded_chunks
    except Exception as e:
        logger.error(f"Error embedding chunks: {str(e)}")
        raise


async def embed_query(query: str) -> List[float]:
    """
    Generate embedding for a query string.
    
    Args:
        query: Query string to embed
        
    Returns:
        Embedding vector for the query
    """
    if not query or not query.strip():
        logger.warning("Received empty query for embedding")
        raise ValueError("Query cannot be empty")
    
    try:
        embeddings = await generate_embeddings([query])
        return embeddings[0]
    except Exception as e:
        logger.error(f"Error embedding query: {str(e)}")
        raise
