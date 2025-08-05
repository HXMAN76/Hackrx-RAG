import os
import json
from pathlib import Path
from dotenv import load_dotenv
import spacy

# Load config from .env
load_dotenv()
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 512))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 50))
SENTENCE_SPLITTER = os.getenv("SENTENCE_SPLITTER", "spacy")

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

def chunk_text(file_path: str):
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"No such file: {file_path}")

    text = path.read_text(encoding="utf-8")
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents]

    chunks = []
    current_chunk = ""
    i = 0

    while i < len(sentences):
        temp_chunk = current_chunk
        start_i = i  # Track position

        # Add as many sentences as possible into current chunk
        while i < len(sentences) and len(temp_chunk) + len(sentences[i]) + 1 <= CHUNK_SIZE:
            temp_chunk += sentences[i] + " "
            i += 1

        # If no new sentence was added (e.g., one sentence too long)
        if i == start_i:
            # Force add long sentence and move on
            temp_chunk = sentences[i]
            i += 1

        chunks.append(temp_chunk.strip())

        # Overlap last CHUNK_OVERLAP characters
        current_chunk = temp_chunk[-CHUNK_OVERLAP:]

    return chunks

def save_chunks(chunks, url: str):
    """
    Save the chunked text segments to a JSON file.

    Args:
        chunks (List[str]): List of text segments.
        url (str): Original document URL.

    Returns:
        str: File path of the saved JSON file.
    """
    if not chunks:
        raise ValueError("No chunks to save")

    temp_dir = Path(__file__).resolve().parent.parent / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    file_path = temp_dir / "chunked_file.json"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)

    return str(file_path)