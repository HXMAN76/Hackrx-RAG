from email import utils
from llama_cloud_services import LlamaParse
import asyncio
import time
import os
from dotenv import load_dotenv
import aiohttp
from pathlib import Path
import tempfile
import logging
import app.utils.chunker as chunker
import app.utils.embedder as embedder


logger = logging.getLogger(__name__)


load_dotenv()
from app.config import (
    LLAMA_API_KEY,
    LLAMA_LANGUAGE,
    LLAMA_FAST_MODE,
    LLAMA_DISABLE_OCR,
    LLAMA_DISABLE_IMG,
    LLAMA_HIDE_HEADERS,
    LLAMA_HIDE_FOOTERS,
    ASYNC_TIMEOUT
)

parser = LlamaParse(
    api_key=LLAMA_API_KEY,
    verbose=True,
    language=LLAMA_LANGUAGE,
    disable_ocr=LLAMA_DISABLE_OCR,
    disable_image_extraction=LLAMA_DISABLE_IMG,
    hide_headers=LLAMA_HIDE_HEADERS,
    hide_footers=LLAMA_HIDE_FOOTERS,
    fast_mode=LLAMA_FAST_MODE,
)
# parser = LlamaParse(
#     api_key=os.getenv("LLAMA_CLOUD_API"),  # can also be set in your env as LLAMA_CLOUD_API_KEY
#     verbose=True,
#     language="en",
#     disable_ocr=True,
#     disable_image_extraction=True,
#     hide_headers=True,
#     hide_footers=True,
#     fast_mode=True,
# )

import mimetypes

async def fetch_document(url: str, timeout: int = ASYNC_TIMEOUT):
    safe_url = url.split('?')[0]
    logger.info(f"Starting download of PDF from {safe_url}")
    file_ext = safe_url.split('.')[-1].lower()
    logger.debug(f"Detected file extension: {file_ext}")
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}')
    temp_path = Path(temp_file.name)

    headers = {'User-Agent': 'HackRx-RAG-System/1.0'}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=timeout, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"Download failed: HTTP {response.status}")
                    return None
                
                with open(temp_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(4096):
                        f.write(chunk)

        logger.info(f"Downloaded {file_ext.upper()} to {temp_path}")
        return temp_path, file_ext
    
    except asyncio.TimeoutError:
        logger.error(f"Timeout after {timeout}s")
    except Exception as e:
        logger.error(f"Error: {e}")
    
    try:
        temp_path.unlink()
    except Exception:
        pass
    
    return None



async def parse_pdf(path):
    documents = await parser.aload_data(path)
    return documents

async def save_pdf(content, url:str):
    temp_dir = Path(__file__).resolve().parent.parent / "temp"
    temp_dir.mkdir(exist_ok=True)
    
    filename = f"pdf_to_text.txt"

    file_path = temp_dir / filename

    # Save content
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(str(content))

    logger.info(f"Saved parsed content to {file_path}")
    return str(file_path) 

async def document_downloader(url: str):
    """
    Download a document (PDF, DOCX, or email) and extract its text.

    Args:
        url: URL of the document

    Returns:
        Extracted text as string, or None if processing fails
    """
    safe_url = url
    if '%' not in url and ('&' in url or '+' in url or '=' in url):
        # Only encode the query part, not the entire URL
        parts = url.split('?', 1)
        if len(parts) > 1:
            base_url, query = parts
            # Don't re-encode percent signs
            safe_url = f"{base_url}?{query}"
    try:
        result = await fetch_document(url)
        if not result:
            logger.error("Failed to download document")
            return None

        doc_path, file_ext = result

        try:
            if file_ext == "pdf":
                pdf_text =  await parse_pdf(doc_path)
                saved_path = await save_pdf(pdf_text, url)
                logger.info(f"Processed PDF file: {doc_path}")
                chunks = chunker.chunk_pdf_text(saved_path)
                chunked_file_path = chunker.save_chunks(chunks, url)
                logger.debug(f"Chunked PDF text into {len(chunks)} segments")
                embedder.embed_chunks(chunked_file_path)
                return chunks
            # elif file_ext in ["docx", "doc"]:
            #     return parse_docx(doc_path)
            elif file_ext in ["eml", "msg"]:
                logger.debug(f"Processing email file: {doc_path}")
                return None
                # return parse_email(doc_path)
            else:
                logger.error(f"Unsupported file type: {file_ext}")
                return None
        finally:
            try:
                Path(doc_path).unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")

    except Exception as e:
        logger.error(f"Error processing document: {e}")
        return None
    