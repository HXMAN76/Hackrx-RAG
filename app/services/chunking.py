import logging
import re
from typing import List, Dict, Any

from app.config import CHUNK_SIZE, CHUNK_OVERLAP
from app.models import Chunk

logger = logging.getLogger(__name__)


def chunk_text(
    text: str, 
    chunk_size: int = CHUNK_SIZE, 
    chunk_overlap: int = CHUNK_OVERLAP, 
    metadata: Dict[str, Any] = None
) -> List[Chunk]:
    """
    Split text into overlapping chunks of specified size.
    
    Args:
        text: The text to split into chunks
        chunk_size: Maximum number of characters per chunk
        chunk_overlap: Number of characters to overlap between chunks
        metadata: Optional metadata to include with each chunk
        
    Returns:
        List of Chunk objects
    """
    if not text or not text.strip():
        logger.warning("Received empty text for chunking")
        return []

    if metadata is None:
        metadata = {}
    
    # Clean text: normalize whitespace and remove excessive newlines
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # If text is shorter than chunk_size, return as a single chunk
    if len(text) <= chunk_size:
        return [Chunk(text=text, metadata=metadata)]
    
    chunks = []
    start = 0
    chunk_id = 0
    
    while start < len(text):
        # Calculate end position of the current chunk
        end = start + chunk_size
        
        # If not at the end of the text, try to find a good breaking point
        if end < len(text):
            # Try to break at sentence boundary within the last 20% of the chunk
            search_start = end - int(chunk_size * 0.2)
            search_text = text[search_start:end]
            
            # Look for sentence endings (., !, ?)
            sentence_match = re.search(r'[.!?]\s+', search_text)
            if sentence_match:
                break_point = search_start + sentence_match.end()
                end = break_point
            else:
                # If no sentence break found, try to break at space
                space_match = text.rfind(' ', search_start, end)
                if space_match > search_start:
                    end = space_match + 1
        
        # Create chunk with unique ID
        chunk_metadata = metadata.copy()
        chunk_metadata["chunk_id"] = chunk_id
        
        chunks.append(Chunk(
            text=text[start:end].strip(),
            metadata=chunk_metadata
        ))
        
        # Move to next chunk with overlap
        start = end - chunk_overlap
        chunk_id += 1
    
    logger.info(f"Split text into {len(chunks)} chunks")
    return chunks


def chunk_by_paragraph(
    text: str, 
    max_chunk_size: int = CHUNK_SIZE, 
    metadata: Dict[str, Any] = None
) -> List[Chunk]:
    """
    Split text into chunks by paragraph, merging small paragraphs as needed.
    
    Args:
        text: The text to split into chunks
        max_chunk_size: Maximum number of characters per chunk
        metadata: Optional metadata to include with each chunk
        
    Returns:
        List of Chunk objects
    """
    if not text or not text.strip():
        return []

    if metadata is None:
        metadata = {}
    
    # Split by paragraph
    paragraphs = re.split(r'\n\s*\n', text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    chunks = []
    current_chunk = ""
    chunk_id = 0
    
    for para in paragraphs:
        # If current paragraph + current chunk exceeds the limit, start a new chunk
        if len(current_chunk) + len(para) > max_chunk_size and current_chunk:
            # Add current chunk to chunks
            chunk_metadata = metadata.copy()
            chunk_metadata["chunk_id"] = chunk_id
            chunks.append(Chunk(text=current_chunk.strip(), metadata=chunk_metadata))
            
            # Reset for next chunk
            current_chunk = para
            chunk_id += 1
        else:
            # Add paragraph to current chunk with a space if needed
            if current_chunk and not current_chunk.endswith(' '):
                current_chunk += " "
            current_chunk += para
    
    # Add the last chunk if there's anything left
    if current_chunk:
        chunk_metadata = metadata.copy()
        chunk_metadata["chunk_id"] = chunk_id
        chunks.append(Chunk(text=current_chunk.strip(), metadata=chunk_metadata))
    
    logger.info(f"Split text into {len(chunks)} paragraph-based chunks")
    return chunks
