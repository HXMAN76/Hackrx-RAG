import os
import re
import json
import hashlib
from typing import List, Dict, Optional
import nltk

# Download sentence tokenizer if not already present
try:
    nltk.download('punkt_tab')
except:
    nltk.download('punkt')

class RAGChunker:
    """
    A chunking class for Retrieval-Augmented Generation (RAG) pipelines.
    Performs section- and document-aware chunking with sentence boundary detection.
    Outputs JSON with rich metadata.
    """

    # Default chunking parameters (in words)
    DEFAULT_CHUNK_SIZE = 768
    DEFAULT_CHUNK_OVERLAP = 100

    # Regex patterns to detect document and section boundaries
    DOCUMENT_PATTERN = re.compile(r'^DOCUMENT: (.+)\.pdf', re.IGNORECASE)
    SECTION_PATTERN = re.compile(r'^(SECTION|PART|ANNEXURE)[^\n]*', re.IGNORECASE)

    def __init__(self, 
                 chunk_size: Optional[int] = None, 
                 chunk_overlap: Optional[int] = None):
        """
        Initialize the chunker with optional custom chunk size and overlap.
        """
        self.chunk_size = chunk_size or self.DEFAULT_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or self.DEFAULT_CHUNK_OVERLAP

    def read_file_lines(self, filepath: str) -> List[str]:
        """
        Reads a text file line by line.
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.readlines()

    def split_sections(self, lines: List[str]) -> List[Dict]:
        """
        Splits the file into sections based on document and section headers.
        Returns list of dicts with {document, section, start_line, end_line, lines}.
        """
        sections = []
        current_doc = None
        current_section = None
        section_start = 0

        for i, line in enumerate(lines):
            stripped = line.strip()

            doc_match = self.DOCUMENT_PATTERN.match(stripped)
            if doc_match:
                # Save prior section if exists
                if current_section is not None:
                    sections.append({
                        'document': current_doc,
                        'section': current_section,
                        'start_line': section_start,
                        'end_line': i - 1,
                        'lines': lines[section_start:i]
                    })
                current_doc = doc_match.group(1) + '.pdf'
                current_section = 'DOCUMENT_START'
                section_start = i

            elif self.SECTION_PATTERN.match(stripped):
                if current_section is not None:
                    sections.append({
                        'document': current_doc,
                        'section': current_section,
                        'start_line': section_start,
                        'end_line': i - 1,
                        'lines': lines[section_start:i]
                    })
                current_section = stripped
                section_start = i

        # Append the last section
        if current_section is not None:
            sections.append({
                'document': current_doc,
                'section': current_section,
                'start_line': section_start,
                'end_line': len(lines) - 1,
                'lines': lines[section_start:]
            })

        return sections

    def preprocess_text(self, text: str) -> str:
        """
        Basic text normalization: normalize whitespace, remove unwanted chars if needed.
        Extend this for more advanced preprocessing if required.
        """
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def sentence_tokenize(self, text: str) -> List[str]:
        """
        Uses NLTK to split text into sentences.
        """
        return nltk.sent_tokenize(text)

    def chunk_sentences(self, sentences: List[str]) -> List[Dict]:
        """
        Chunks sentences into overlapping word-based chunks while preserving sentence boundaries.
        Each chunk approx chunk_size words, with chunk_overlap overlap.
        """
        chunks = []
        chunk_id = 1
        i = 0  # index of sentences

        # Precompute sentence word counts for efficiency
        sent_word_counts = [len(sent.split()) for sent in sentences]

        total_sents = len(sentences)
        while i < total_sents:
            # Accumulate sentences until chunk_size reached or exceeded
            chunk_sents = []
            chunk_word_count = 0
            j = i
            while j < total_sents and chunk_word_count < self.chunk_size:
                chunk_sents.append(sentences[j])
                chunk_word_count += sent_word_counts[j]
                j += 1

            chunk_text = ' '.join(chunk_sents)
            chunk_text = self.preprocess_text(chunk_text)

            # Compute hash for deduplication or referencing
            chunk_hash = hashlib.sha256(chunk_text.encode('utf-8')).hexdigest()

            # Build chunk dictionary (metadata to be added later)
            chunks.append({
                'chunk_id': chunk_id,
                'text': chunk_text,
                'word_count': chunk_word_count,
                'char_count': len(chunk_text),
                'hash': chunk_hash
            })

            chunk_id += 1

            # Move start index for next chunk, considering overlap
            # Move forward by chunk_size - chunk_overlap words in sentences
            moved_words = 0
            k = i
            while k < total_sents and moved_words < (self.chunk_size - self.chunk_overlap):
                moved_words += sent_word_counts[k]
                k += 1
            if k == i:  # Could happen if a single sentence is very long
                k = i + 1
            i = k

        return chunks

    def chunk_section(self, section: Dict, source_file: str) -> List[Dict]:
        """
        Chunks a section dict into overlapping chunks, preserving sentence boundaries.
        Adds rich metadata including source file, document, section, and chunk stats.
        """
        text = ''.join(section['lines'])
        text = self.preprocess_text(text)
        sentences = self.sentence_tokenize(text)

        chunked_sentences = self.chunk_sentences(sentences)

        enriched_chunks = []
        for c in chunked_sentences:
            enriched_chunks.append({
                'document': section['document'],
                'section': section['section'],
                'chunk_id': c['chunk_id'],
                'text': c['text'],
                'word_count': c['word_count'],
                'char_count': c['char_count'],
                'metadata': {
                    'source': os.path.basename(source_file)
                },
                # For simplicity, start_line and end_line from section
                'start_line': section['start_line'],
                'end_line': section['end_line'],
                'hash': c['hash'],
            })

        return enriched_chunks

    def chunk_file_to_json(self, input_path: str, output_path: str):
        """
        Main method to chunk the input file and save chunks to JSON.
        """
        print(f"Reading file: {input_path}")
        lines = self.read_file_lines(input_path)

        print("Splitting into sections...")
        sections = self.split_sections(lines)

        print(f"Chunking {len(sections)} sections...")
        all_chunks = []
        for section in sections:
            # Skip if section missing document or section info
            if not section['document'] or not section['section']:
                continue
            section_chunks = self.chunk_section(section, input_path)
            all_chunks.extend(section_chunks)

        print(f"Writing {len(all_chunks)} chunks to {output_path}...")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_chunks, f, ensure_ascii=False, indent=2)

        print(f"Chunking complete. Output saved at: {output_path}")



# Example Usage
if __name__ == '__main__':
    import sys

    # You can pass input and output file paths as args or hardcode them here
    input_file = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'combined_dataset.txt')
    output_file = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'combined_chunks.json')

    chunker = RAGChunker(
        chunk_size=768,      # Optimal chunk size balancing context and retrieval
        chunk_overlap=100    # Overlap to preserve context between chunks
    )
    chunker.chunk_file_to_json(input_file, output_file)
