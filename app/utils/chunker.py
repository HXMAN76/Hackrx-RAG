import json
import spacy 
from pathlib import Path

# Load spaCy model globally for efficiency
nlp = spacy.load("en_core_web_sm")

def chunk_pdf_text(file_path: str, min_chunk_len=30):
    """
    Chunk the content of a saved text file using spaCy noun phrase chunking.

    Args:
        file_path (str): Path to the text file.
        min_chunk_len (int): Minimum character length to consider a valid chunk.

    Returns:
        List[str]: List of chunked text segments.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"No such file: {file_path}")

    text = path.read_text(encoding="utf-8")
    doc = nlp(text)

    chunks = []

    # Collect noun chunks
    for np in doc.noun_chunks:
        chunk_text = np.text.strip()
        if len(chunk_text) >= min_chunk_len:
            chunks.append(chunk_text)

    return chunks

def save_chunks(chunks, url: str):
    """    Save the chunked text segments to a file.

    Args:
        chunks (List[str]): List of text segments.
        url (str): URL of the original document for reference.

    Returns:
        str: Path to the saved file containing chunks.
    """
    if not chunks:
        raise ValueError("No chunks to save")
    temp_dir = Path(__file__).resolve().parent.parent / "temp"
    temp_dir.mkdir(exist_ok=True)

    # Create unique filename
    filename = f"chunked_file.json"

    file_path = temp_dir / filename

    # Save the chunks
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)

    return str(file_path)