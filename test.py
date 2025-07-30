import fitz  # PyMuPDF
import pdfplumber

def extract_text_and_tables(pdf_path):
    text_chunks = []
    table_chunks = []

    # Extract text using fitz (fast and layout-aware)
    doc = fitz.open(pdf_path)
    for page in doc:
        text = page.get_text("text")
        if text.strip():
            text_chunks.append(text.strip())

    # Extract tables using pdfplumber
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if table:
                    table_chunks.append(table)

    return text_chunks, table_chunks
