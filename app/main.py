import logging
from contextlib import asynccontextmanager
import asyncio
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import app.utils.downloader as parser
import uvicorn

from app.config import APP_NAME, APP_VERSION, LOG_LEVEL
from app.routes import rag

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI.
    Handles startup and shutdown events.
    """
    # Startup: Pre-load models and establish connections
    # from app.services.embedding import get_embedding_model
    # from app.services.qdrant import get_qdrant_service
    
    logger.info("Initializing services...")
    
    # Load embedding model at startup (will be cached)
    # get_embedding_model()
    
    # # Initialize Qdrant connection
    # qdrant_service = await get_qdrant_service()
    
    logger.info("All services initialized successfully")
    
    yield
    
    # Shutdown: Cleanup resources
    logger.info("Shutting down...")

# Initialize FastAPI app
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="A fast and accurate RAG system API",
    # lifespan=,
    # Document authentication methods
    openapi_tags=[
        {
            "name": "RAG",
            "description": "Retrieval Augmented Generation endpoints"
        }
    ],
    # Security schemes for Swagger UI
    swagger_ui_parameters={"defaultModelsExpandDepth": -1}
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add routes with API version prefix
app.include_router(rag.router, prefix="/api/v1", tags=["RAG"])

# Add request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Middleware to measure and log request processing time.
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Add timing header
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log request time for monitoring
    logger.info(f"Request processed in {process_time:.2f}s: {request.method} {request.url.path}")
    
    return response
  
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint.
    
    Returns:
        Basic API information
    """
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "description": "A fast and accurate RAG system API",
        "docs_url": "/docs"
    }
    
if __name__ == "__main__":
    # Run the app with uvicorn when executed directly
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Set to False in production
        log_level=LOG_LEVEL.lower()
    )

