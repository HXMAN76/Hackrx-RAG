import asyncio
import logging
import time
from typing import Optional, List, Union
import re
from urllib.parse import unquote, quote

from fastapi import APIRouter, HTTPException, Depends, Header, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import HttpUrl, AnyHttpUrl

from app.config import TOP_K_RETRIEVAL, ENABLE_AUTH, API_KEY_HEADER, APP_VERSION, AUTH_TOKEN
from app.models import QueryRequest, QueryResponse, BatchQueryRequest, BatchQueryResponse, HealthResponse
from app.services.chunking import chunk_text
from app.services.embedding import embed_chunks, embed_query
from app.services.llm import get_llm_service
from app.services.qdrant import get_qdrant_service
from app.utils.downloader import get_document_text

router = APIRouter(prefix="/hackrx")
logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


async def verify_auth(
    api_key: Optional[str] = Header(None, alias=API_KEY_HEADER),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
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


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status
    """
    return HealthResponse(status="ok", version=APP_VERSION)


@router.post("/run", response_model=Union[QueryResponse, BatchQueryResponse])
async def run_rag(
    request: QueryRequest,
    auth: Optional[str] = Depends(verify_auth)
):
    """
    Process a RAG query or redirect to batch processing if appropriate format.
    
    This endpoint handles both single queries and batch queries to maintain compatibility
    with different client implementations.
    
    Args:
        request: Query request with either query/doc_url or documents/questions format
        auth: Authorization result from verify_auth dependency
        
    Returns:
        Generated answer and sources or batch results
    """
    # Check if this is actually a batch request in the alternate format
    if request.questions and request.documents:
        logger.info(f"Detected batch request format in /run endpoint - processing as batch")
        # Convert to BatchQueryRequest and call batch processing
        batch_request = BatchQueryRequest(
            documents=request.documents,
            questions=request.questions,
            top_k=request.top_k if request.top_k else TOP_K_RETRIEVAL
        )
        return await run_batch_rag(batch_request, auth)
        
    # If we get here, it's not a batch request, so query is required
    if not request.query:
        raise HTTPException(
            status_code=400,
            detail="For single query format, 'query' field is required. For batch format, use both 'documents' and 'questions' fields."
        )
        
    start_time = time.time()
    logger.info(f"Processing RAG request: {request.query[:50]}...")
    
    try:
        # Step 1: Process document if URL is provided
        document_chunks = []
        doc_url = request.doc_url
        
        # Support both doc_url and documents fields
        if not doc_url and request.documents:
            doc_url = request.documents
            
        if doc_url:
            # Download and extract text from document
            document_text = await get_document_text(str(doc_url))
            if not document_text:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to process document"
                )
            
            # Chunk the document
            chunks = chunk_text(
                document_text, 
                metadata={"url": str(doc_url)}
            )
            
            # Generate embeddings for chunks
            embedded_chunks = await embed_chunks(chunks)
            
            # Store chunks in vector database
            qdrant_service = await get_qdrant_service()
            await qdrant_service.upsert_chunks(embedded_chunks)
        
        # Step 2: Generate embedding for the query
        query_embedding = await embed_query(request.query)
        
        # Step 3: Retrieve relevant chunks
        qdrant_service = await get_qdrant_service()
        top_k = request.top_k if request.top_k else TOP_K_RETRIEVAL
        retrieved_chunks = await qdrant_service.search(
            query_vector=query_embedding,
            top_k=top_k,
            filter_conditions={"url": str(doc_url)} if doc_url else None
        )
        
        # Step 4: Generate answer using LLM
        llm_service = get_llm_service()
        answer = await llm_service.generate_rag_response(
            query=request.query,
            context_chunks=retrieved_chunks
        )
        
        # Prepare sources for response
        sources = []
        for chunk in retrieved_chunks:
            sources.append({
                "text": chunk["text"][:200] + "...",  # Truncate for response
                "metadata": chunk["metadata"],
                "score": chunk["score"]
            })
        
        # Calculate processing time
        processing_time = time.time() - start_time
        logger.info(f"RAG request processed in {processing_time:.2f} seconds")
        
        # Return response
        return QueryResponse(
            answer=answer,
            sources=sources,
            processing_time=processing_time
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing RAG request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )


@router.post("/batch", response_model=BatchQueryResponse)
async def run_batch_rag(
    request: BatchQueryRequest,
    auth: Optional[str] = Depends(verify_auth)
):
    """
    Process multiple RAG queries on the same document.
    
    Args:
        request: Batch query request with document URL and list of questions
        auth: Authorization result from verify_auth dependency
        
    Returns:
        Generated answers and sources for each question
    """
    start_time = time.time()
    logger.info(f"Processing batch RAG request with {len(request.questions)} questions")
    
    try:
        # Step 1: Process document
        # Extract document URL, handling potential parsing issues with complex URLs
        document_url = str(request.documents)
        
        # Handle URL encoding issues with Azure blob storage SAS tokens
        if '%' in document_url:
            document_url = unquote(document_url)
        
        # Log only part of the URL for security if it contains a SAS token
        safe_url_for_logs = document_url.split('?')[0] if '?' in document_url else document_url
        logger.info(f"Processing document at {safe_url_for_logs}")
        
        document_text = await get_document_text(document_url)
        if not document_text:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to process document"
            )
        
        # Step 2: Chunk the document
        chunks = chunk_text(
            document_text, 
            metadata={"url": document_url}
        )
        
        # Step 3: Generate embeddings for chunks
        embedded_chunks = await embed_chunks(chunks)
        
        # Step 4: Store chunks in vector database
        qdrant_service = await get_qdrant_service()
        await qdrant_service.upsert_chunks(embedded_chunks)
        
        # Step 5: Process each question in parallel
        tasks = []
        for question in request.questions:
            tasks.append(
                process_single_question(
                    query=question, 
                    doc_url=document_url,
                    top_k=request.top_k if request.top_k else TOP_K_RETRIEVAL
                )
            )
        
        # Wait for all questions to be processed
        answers = await asyncio.gather(*tasks)
        
        # Calculate total processing time
        total_processing_time = time.time() - start_time
        logger.info(f"Batch RAG request processed in {total_processing_time:.2f} seconds")
        
        # Return response
        return BatchQueryResponse(
            answers=answers,
            total_processing_time=total_processing_time
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing batch RAG request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing batch request: {str(e)}"
        )


async def process_single_question(query: str, doc_url: str, top_k: int) -> QueryResponse:
    """
    Process a single question using RAG.
    
    Args:
        query: Question to answer
        doc_url: URL of the document to use
        top_k: Number of chunks to retrieve
        
    Returns:
        Generated answer and sources
    """
    start_time = time.time()
    
    try:
        # Generate embedding for the query
        query_embedding = await embed_query(query)
        
        # Retrieve relevant chunks
        qdrant_service = await get_qdrant_service()
        retrieved_chunks = await qdrant_service.search(
            query_vector=query_embedding,
            top_k=top_k,
            filter_conditions={"url": doc_url}
        )
        
        # Generate answer using LLM
        llm_service = get_llm_service()
        answer = await llm_service.generate_rag_response(
            query=query,
            context_chunks=retrieved_chunks
        )
        
        # Prepare sources for response
        sources = []
        for chunk in retrieved_chunks:
            sources.append({
                "text": chunk["text"][:200] + "...",  # Truncate for response
                "metadata": chunk["metadata"],
                "score": chunk["score"]
            })
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Return response
        return QueryResponse(
            answer=answer,
            sources=sources,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error processing question '{query[:30]}...': {str(e)}")
        raise
