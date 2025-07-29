import asyncio
import logging
from typing import List, Dict, Optional, Any

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct

from app.config import (
    QDRANT_URL, 
    QDRANT_API_KEY, 
    QDRANT_COLLECTION,
    VECTOR_SIZE, 
    VECTOR_DISTANCE
)
from app.models import EmbeddedChunk

logger = logging.getLogger(__name__)


class QdrantService:
    """Service for interacting with Qdrant vector database."""
    
    def __init__(
        self, 
        url: str = QDRANT_URL,
        api_key: Optional[str] = QDRANT_API_KEY,
        collection_name: str = QDRANT_COLLECTION,
    ):
        self.url = url
        self.api_key = api_key
        self.collection_name = collection_name
        self.client = None
    
    async def connect(self) -> None:
        """Establish connection to Qdrant."""
        try:
            self.client = QdrantClient(
                url=self.url,
                api_key=self.api_key,
                timeout=10.0  # Default timeout
            )
            # Test connection
            self.client.get_collections()
            logger.info(f"Successfully connected to Qdrant at {self.url}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {str(e)}")
            raise
    
    async def create_collection_if_not_exists(self) -> None:
        """Create the collection if it doesn't already exist."""
        if not self.client:
            await self.connect()
            
        try:
            collections = self.client.get_collections()
            collection_names = [collection.name for collection in collections.collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating collection: {self.collection_name}")
                
                # Set distance metric based on config
                if VECTOR_DISTANCE.upper() == "COSINE":
                    distance = Distance.COSINE
                elif VECTOR_DISTANCE.upper() == "EUCLID":
                    distance = Distance.EUCLID
                elif VECTOR_DISTANCE.upper() == "DOT":
                    distance = Distance.DOT
                else:
                    distance = Distance.COSINE
                    logger.warning(f"Unknown distance metric: {VECTOR_DISTANCE}, using COSINE")
                
                # Create the collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=VECTOR_SIZE,
                        distance=distance
                    )
                )
                logger.info(f"Collection {self.collection_name} created successfully")
            else:
                logger.info(f"Collection {self.collection_name} already exists")
                
        except Exception as e:
            logger.error(f"Error creating collection: {str(e)}")
            raise
    
    async def upsert_chunks(self, chunks: List[EmbeddedChunk]) -> List[str]:
        """
        Insert or update chunks in the vector database.
        
        Args:
            chunks: List of EmbeddedChunk objects to insert
            
        Returns:
            List of IDs for the inserted chunks
        """
        if not chunks:
            return []
            
        if not self.client:
            await self.connect()
        
        # Ensure collection exists
        await self.create_collection_if_not_exists()
        
        try:
            # Prepare points for upserting
            points = []
            chunk_ids = []
            
            for i, chunk in enumerate(chunks):
                try:
                    # Generate a numeric ID for the chunk (Qdrant requires unsigned integer or UUID)
                    numeric_id = i + 1  # Start with 1 to avoid 0
                    
                    # For URL-based chunks, generate a deterministic numeric ID from the URL
                    if "url" in chunk.metadata:
                        url = str(chunk.metadata['url'])
                        import hashlib
                        # Generate a hash of the URL + chunk index
                        hash_input = f"{url}_{i}"
                        # Convert the hash to a numeric ID (first 10 digits of int representation of hash)
                        hash_obj = hashlib.md5(hash_input.encode())
                        # Take first 10 digits of the integer representation of the hash
                        # This ensures we stay within uint64 range for Qdrant
                        numeric_id = int(hash_obj.hexdigest(), 16) % (2**63 - 1)
                    
                    # Original chunk ID for tracking (used in returned IDs)
                    original_chunk_id = str(chunk.metadata.get("chunk_id", f"chunk_{i}"))
                    
                    # Store the string ID in metadata for reference
                    chunk.metadata["original_id"] = original_chunk_id
                    
                    # Store the numeric ID for return
                    chunk_ids.append(str(numeric_id))
                    
                    # Log the ID being used
                    logger.debug(f"Using numeric chunk ID: {numeric_id} for original ID: {original_chunk_id}")
                    
                    points.append(
                        PointStruct(
                            id=numeric_id,
                            vector=chunk.embedding,
                            payload={
                                "text": chunk.text,
                                **chunk.metadata
                            }
                        )
                    )
                except Exception as e:
                    logger.error(f"Error processing chunk {i}: {str(e)}")
                    # Continue with other chunks
            
            # Upsert in batches of 100
            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
                
            logger.info(f"Upserted {len(chunks)} chunks to Qdrant")
            return chunk_ids
            
        except Exception as e:
            logger.error(f"Error upserting chunks: {str(e)}")
            raise
    
    async def search(
        self, 
        query_vector: List[float], 
        top_k: int = 3, 
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in the database.
        
        Args:
            query_vector: The query embedding vector
            top_k: Number of results to return
            filter_conditions: Optional filter conditions
            
        Returns:
            List of search results with text and metadata
        """
        if not self.client:
            await self.connect()
            
        try:
            # Build filter if provided
            search_filter = None
            
            if filter_conditions:
                # Remove URL from filter conditions if present to avoid index errors
                # URL is stored in payload but not indexed for keyword search
                safe_filter = {k: v for k, v in filter_conditions.items() if k != 'url'}
                
                # Convert remaining filter_conditions to Qdrant filter format
                filter_clauses = []
                for key, value in safe_filter.items():
                    filter_clauses.append(models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=value)
                    ))
                    
                if filter_clauses:
                    search_filter = models.Filter(
                        must=filter_clauses
                    )
                
                # If URL was in original filter, log that we're ignoring it
                if 'url' in filter_conditions and filter_conditions['url']:
                    logger.warning("URL filter removed from search to avoid index errors. " 
                                  "Results will include all documents.")
            
            # Perform the search
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=search_filter
            )
            
            # Extract relevant information from results
            results = []
            for hit in search_results:
                results.append({
                    "text": hit.payload.get("text", ""),
                    "score": hit.score,
                    "metadata": {k: v for k, v in hit.payload.items() if k != "text"}
                })
            
            logger.info(f"Retrieved {len(results)} results for query")
            return results
            
        except Exception as e:
            logger.error(f"Error searching in Qdrant: {str(e)}")
            raise


# Global instance for reuse
_qdrant_service = None


async def get_qdrant_service() -> QdrantService:
    """
    Get or create a QdrantService instance.
    
    Returns:
        QdrantService instance
    """
    global _qdrant_service
    
    if _qdrant_service is None:
        _qdrant_service = QdrantService()
        await _qdrant_service.connect()
        await _qdrant_service.create_collection_if_not_exists()
    
    return _qdrant_service
