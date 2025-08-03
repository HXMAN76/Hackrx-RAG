import app.utils.downloader as fetcher
from fastapi import APIRouter, HTTPException, Depends, Header, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
from app.config import(
  API_KEY_HEADER,
  AUTH_TOKEN,
  ENABLE_AUTH,
  APP_VERSION,
)

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


@router.post("/document", tags=["RAG"], dependencies=[Depends(verify_auth)])
async def get_document_text(url: str):
    """
    Fetch and process document text from a given URL.
    
    Args:
        url: URL of the document to fetch
    Returns:
        Processed text content of the document
    """
    document = await fetcher.document_downloader(url)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"text": document}  # ✅ Return the parsed content

    #processed_text = await fetcher.process_document_text(document)
    #return {"text": processed_text}