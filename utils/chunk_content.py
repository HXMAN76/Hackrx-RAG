# Modularized and commented chunking logic for RAG
import os
import re
import json
from typing import List, Dict

class RAGChunker:
    """
    A class to chunk large text files for Retrieval-Augmented Generation (RAG) pipelines.
    Splits by document/section, then into overlapping word windows, and outputs JSON with metadata.
    """
    # Default parameters for chunking
    CHUNK_SIZE = 512
    CHUNK_OVERLAP = 128
    SECTION_PATTERN = re.compile(r'^(SECTION|PART|ANNEXURE)[^\n]*', re.IGNORECASE)
    DOCUMENT_PATTERN = re.compile(r'^DOCUMENT: (.+)\.pdf', re.IGNORECASE)

    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        """
        Initialize the chunker with optional custom chunk size and overlap.
        """
        self.chunk_size = chunk_size or self.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or self.CHUNK_OVERLAP

    def read_file_lines(self, filepath: str) -> List[str]:
        """
        Read all lines from a text file.
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.readlines()

    def split_sections(self, lines: List[str]) -> List[Dict]:
        """
        Splits the file into sections based on headings and document markers.
        Returns a list of dicts: {document, section, start_line, end_line, lines}
        """
        sections = []
        current_doc = None
        current_section = None
        section_start = 0
        for i, line in enumerate(lines):
            doc_match = self.DOCUMENT_PATTERN.match(line.strip())
            if doc_match:
                # Save previous section if exists
                if current_section is not None:
                    sections.append({
                        'document': current_doc,
                        'section': current_section,
                        'start_line': section_start,
                        'end_line': i-1,
                        'lines': lines[section_start:i]
                    })
                current_doc = doc_match.group(1) + '.pdf'
                current_section = 'DOCUMENT_START'
                section_start = i
            elif self.SECTION_PATTERN.match(line.strip()):
                if current_section is not None:
                    sections.append({
                        'document': current_doc,
                        'section': current_section,
                        'start_line': section_start,
                        'end_line': i-1,
                        'lines': lines[section_start:i]
                    })
                current_section = line.strip()
                section_start = i
        # Add last section
        if current_section is not None:
            sections.append({
                'document': current_doc,
                'section': current_section,
                'start_line': section_start,
                'end_line': len(lines)-1,
                'lines': lines[section_start:]
            })
        return sections

    def chunk_section(self, section: Dict, source_file: str) -> List[Dict]:
        """
        Chunk a section into overlapping word windows, with metadata.
        """
        text = ''.join(section['lines'])
        words = text.split()
        chunks = []
        i = 0
        chunk_id = 1
        while i < len(words):
            chunk_words = words[i:i+self.chunk_size]
            chunk_text = ' '.join(chunk_words)
            chunk = {
                'document': section['document'],
                'section': section['section'],
                'chunk_id': chunk_id,
                'text': chunk_text,
                'start_line': section['start_line'],  # For simplicity, use section start
                'end_line': section['end_line'],
                'metadata': {
                    'source': os.path.basename(source_file)
                }
            }
            chunks.append(chunk)
            chunk_id += 1
            if i + self.chunk_size >= len(words):
                break
            i += self.chunk_size - self.chunk_overlap
        return chunks

    def chunk_file_to_json(self, input_path: str, output_path: str):
        """
        Main method to chunk a file and write the output as JSON.
        """
        lines = self.read_file_lines(input_path)
        sections = self.split_sections(lines)
        all_chunks = []
        for section in sections:
            # Skip empty or None document/section
            if not section['document'] or not section['section']:
                continue
            section_chunks = self.chunk_section(section, input_path)
            all_chunks.extend(section_chunks)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_chunks, f, ensure_ascii=False, indent=2)
        print(f"Chunked data written to {output_path} ({len(all_chunks)} chunks)")

# Example usage
if __name__ == "__main__":
    # Set input and output file paths
    input_file = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'combined_dataset.txt')
    output_file = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'combined_chunks.json')
    # Create a chunker instance (default chunk size/overlap)
    chunker = RAGChunker()
    chunker.chunk_file_to_json(input_file, output_file)