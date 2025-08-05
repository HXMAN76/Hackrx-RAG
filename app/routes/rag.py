import app.utils.downloader__ as fetcher
import app.service.chunker as chunker
import app.service.embedder as embedder
import app.service.vector_store as vector_store
import app.service.retrival as retrival
from fastapi import APIRouter, HTTPException, Depends, Header, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
from app.config import(
  API_KEY_HEADER,
  AUTH_TOKEN,
  ENABLE_AUTH,
  APP_VERSION,
)
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/hackrx")
logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)
async def verify_auth(
    api_key= Header(None, alias=API_KEY_HEADER),
    credentials = Security(security)
):
    """
    Verify authentication using either API key or Bearer token.
    
    Args:
        api_key: API key from request header
        credentials: Bearer token credentials
        
    Raises:
        HTTPException: If authentication is enabled and both API key and Bearer token are invalid
    """
    if not ENABLE_AUTH:
        return
    
    # Check Bearer token
    if credentials is not None:
        if credentials.scheme.lower() == "bearer" and credentials.credentials == AUTH_TOKEN:
            return
    
    # Check API key as fallback
    if api_key:
        # In a real-world scenario, you'd verify against a secure store
        # For demo purposes, we'll accept any non-empty API key
        return
    
    # If we got here, authentication failed
    raise HTTPException(
        status_code=401,
        detail="Authentication required. Provide valid Bearer token or API key."
    )

# @router.get("/health", response_model=HealthResponse)
# async def health_check():
#     """
#     Health check endpoint.
    
#     Returns:
#         Health status
#     """
#     return HealthResponse(status="ok", version=APP_VERSION)
class RAGRequest(BaseModel):
    documents: str
    questions: List[str]


@router.post("/run", tags=["RAG"], dependencies=[Depends(verify_auth)])
async def run_rag(request: RAGRequest):
    """
    Runs the batch processing pipeline for a document URL (eml, .pdf, .docx).
    args:
        url: Document URL to process
    Returns:
        dict: Processing status
    Raises:
        HTTPException: If document not found or processing fails
    """
    isProcessed = await vectorize(request.documents)
    if not isProcessed:
        raise HTTPException(status_code=500, detail="Processing failed")
    
    result = retrival.llm_inference(request.questions)
    if not result:
        raise HTTPException(status_code=404, detail="No answers found for the provided questions")
    return result


async def vectorize(url: str):
    """
    End-to-end processing pipeline:
    - Download document
    - Chunk text
    - Save chunks
    - Embed chunks
    - Upload vectors to Qdrant
    """
    document = await fetcher.document_downloader(url)
    logger.info(f"Fetched document from URL: {url}")
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    chunks = chunker.chunk_text(document)
    logger.info(f"Chunking completed. Total chunks: {len(chunks)}")

    try:
        chunked_file_path = chunker.save_chunks(chunks, url)
        logger.info(f"Chunked text saved. Path: {chunked_file_path}")

        embed_path = embedder.embed_chunks(chunked_file_path, source_file=url)
        logger.info(f"Embedding completed. Path: {embed_path}")

        vector_store.upload_qdrant_ready_file(embed_path)
        logger.info(f"Vectors uploaded to Qdrant collection '{vector_store.COLLECTION_NAME}'.")

    except Exception as e:
        logger.error(f"Error during processing: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    return {"retrieval": True}
