from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, HttpUrl, AnyHttpUrl


class Document(BaseModel):
    """Represents a document to be processed."""
    url: HttpUrl = Field(..., description="URL of the PDF document to process")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata for the document")


class Chunk(BaseModel):
    """Represents a text chunk from a document."""
    text: str = Field(..., description="Text content of the chunk")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata associated with the chunk")


class EmbeddedChunk(Chunk):
    """Represents a text chunk with its vector embedding."""
    embedding: List[float] = Field(..., description="Vector embedding of the chunk")


class QueryRequest(BaseModel):
    """Request model for RAG queries."""
    query: Optional[str] = Field(None, description="The user query to process")
    doc_url: Optional[HttpUrl] = Field(None, description="Optional URL to a document to process")
    top_k: int = Field(3, description="Number of chunks to retrieve")
    
    # For compatibility with the alternate format
    documents: Optional[Union[HttpUrl, AnyHttpUrl, str]] = Field(None, description="URL of the document to process (alternate format)")
    questions: Optional[List[str]] = Field(None, description="List of questions to answer about the document (alternate format)")


class BatchQueryRequest(BaseModel):
    """Request model for batch RAG queries on a single document."""
    documents: Union[HttpUrl, AnyHttpUrl, str] = Field(..., description="URL of the document to process")
    questions: List[str] = Field(..., description="List of questions to answer about the document")
    top_k: int = Field(3, description="Number of chunks to retrieve per question")


class QueryResponse(BaseModel):
    """Response model for RAG queries."""
    answer: str = Field(..., description="Generated answer based on the query and retrieved context")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Source documents used in answering")
    processing_time: float = Field(..., description="Processing time in seconds")


class BatchQueryResponse(BaseModel):
    """Response model for batch RAG queries."""
    answers: List[QueryResponse] = Field(..., description="List of answers for each question")
    total_processing_time: float = Field(..., description="Total processing time in seconds")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field("ok", description="Service status")
    version: str = Field(..., description="API version")
