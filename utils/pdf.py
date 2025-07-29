import fitz
import pdfplumber
import re

def extract_headings_and_text(pdf_path):
    doc = fitz.open(pdf_path)
    sections = []
    current_section = {'title': '', 'content': []}

    for page in doc:
        blocks = page.get_text("dict")['blocks']
        for block in blocks:
            if 'lines' not in block:
                continue
            for line in block['lines']:
                line_text = " ".join([span['text'] for span in line['spans']]).strip()
                if not line_text:
                    continue
                # Detect headings (all caps or starts with "SECTION")
                if re.match(r'^(SECTION|PART|ANNEXURE|TABLE)[\sA-Z0-9\-()]+$', line_text.strip()):
                    if current_section['title']:
                        sections.append(current_section)
                    current_section = {'title': line_text.strip(), 'content': []}
                else:
                    current_section['content'].append(line_text.strip())
    if current_section['title']:
        sections.append(current_section)
    return sections

def extract_tables(pdf_path):
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_tables = page.extract_tables()
            for table in page_tables:
                headers = table[0]
                for row in table[1:]:
                    if any(row):
                        entry = {headers[i]: row[i] for i in range(len(headers)) if i < len(row)}
                        tables.append(entry)
    return tables

def convert_table_to_sentences(table_entries):
    sentences = []
    for row in table_entries:
        row_parts = []
        for heading, value in row.items():
            if heading and value:
                row_parts.append(f"{heading.strip()}: {value.strip()}")
        sentence = ", ".join(row_parts)
        if sentence:
            sentences.append(sentence)
    return sentences

def save_to_txt(sections, tables, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        for sec in sections:
            f.write(f"[{sec['title']}]\n")
            for para in sec['content']:
                f.write(para + "\n")
            f.write("\n")

        if tables:
            f.write("\n[TABLES]\n")
            for sentence in convert_table_to_sentences(tables):
                f.write(sentence + "\n")

# === Run the parser ===
pdf_path = "BAJHLIP23020V012223.pdf"
sections = extract_headings_and_text(pdf_path)
tables = extract_tables(pdf_path)
save_to_txt(sections, tables, "parsed_insurance_output.txt")
