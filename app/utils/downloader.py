import asyncio
import logging
import tempfile
import time
from pathlib import Path
from typing import Optional, Union

import aiohttp
import fitz  # PyMuPDF

from app.config import ASYNC_TIMEOUT

logger = logging.getLogger(__name__)


async def fetch_pdf(url: str, timeout: int = ASYNC_TIMEOUT) -> Optional[Path]:
    """
    Asynchronously download a PDF file from a URL and return the path to the local file.
    
    Args:
        url: URL of the PDF to download
        timeout: Timeout for the HTTP request in seconds
        
    Returns:
        Path to the downloaded PDF file or None if download fails
    """
    start_time = time.time()
    
    # For security and logging, only show part of the URL (especially if it contains SAS tokens)
    safe_url_for_logs = url.split('?')[0] if '?' in url else url
    logger.info(f"Starting download of PDF from {safe_url_for_logs}")
    
    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    temp_path = Path(temp_file.name)
    
    try:
        # Handle Azure blob storage URLs with SAS tokens
        headers = {
            'User-Agent': 'HackRx-RAG-System/1.0',
        }
        
        # Use a longer timeout for larger files
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=timeout, headers=headers, allow_redirects=True) as response:
                if response.status != 200:
                    logger.error(f"Failed to download PDF: HTTP {response.status}")
                    return None
                
                # Write the PDF data to the temp file
                data = await response.read()
                with open(temp_path, 'wb') as f:
                    f.write(data)
                
        download_time = time.time() - start_time
        logger.info(f"PDF downloaded in {download_time:.2f} seconds to {temp_path}")
        return temp_path
        
    except asyncio.TimeoutError:
        logger.error(f"Timeout downloading PDF after {timeout} seconds")
        return None
    except Exception as e:
        logger.error(f"Error downloading PDF: {str(e)}")
        return None


def extract_text_from_pdf(pdf_path: Union[str, Path]) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text as a string
    """
    try:
        doc = fitz.open(pdf_path)
        text = ""
        
        for page in doc:
            text += page.get_text()
            
        logger.info(f"Extracted {len(text)} characters from PDF with {len(doc)} pages")
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return ""
    finally:
        # Clean up
        if 'doc' in locals():
            doc.close()


async def get_document_text(url: str) -> Optional[str]:
    """
    Download a PDF and extract its text.
    
    Args:
        url: URL of the PDF to process
        
    Returns:
        Extracted text or None if processing fails
    """
    # Handle URL encoding for special characters in SAS tokens
    # Azure blob storage URLs often have special characters that need proper handling
    safe_url = url
    
    # Handle already encoded URLs to avoid double encoding
    if '%' not in url and ('&' in url or '+' in url or '=' in url):
        # Only encode the query part, not the entire URL
        parts = url.split('?', 1)
        if len(parts) > 1:
            base_url, query = parts
            # Don't re-encode percent signs
            safe_url = f"{base_url}?{query}"
    
    try:
        pdf_path = await fetch_pdf(safe_url)
        if not pdf_path:
            logger.error(f"Failed to download PDF from URL")
            return None
        
        try:
            return extract_text_from_pdf(pdf_path)
        finally:
            # Clean up temporary file
            try:
                Path(pdf_path).unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {pdf_path}: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        return None
