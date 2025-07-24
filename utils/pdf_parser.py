import os
import logging
from pathlib import Path
from typing import Dict, List, Any
import PyPDF2
import tabula

# Configure logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFParser:
    """Class to parse PDF files and extract text and tables."""
    
    def __init__(self, pdf_path: str):
        """Initialize with the path to a PDF file."""
        self.pdf_path = pdf_path
        
    def parse_pdf(self) -> Dict[str, Any]:
        """Parse PDF and extract text and tables."""
        result = {
            "text": self._extract_text(),
            "tables": self._extract_tables()
        }
        return result
        
    def _extract_text(self) -> str:
        """Extract text from PDF."""
        text = ""
        with open(self.pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text() + "\n"
        return text
        
    def _extract_tables(self) -> List[Any]:
        """Extract tables from PDF using tabula."""
        try:
            tables = tabula.read_pdf(self.pdf_path, pages='all', multiple_tables=True)
            return tables
        except Exception as e:
            logger.warning(f"Failed to extract tables: {str(e)}")
            return []

def table_to_text(table: Any) -> str:
    """Convert a table to text representation."""
    return str(table)

def process_directory(input_dir: str, output_path: str) -> None:
  """
  Process all PDF files in a directory and save their content to a single text file.
  
  Args:
    input_dir: Directory containing PDF files
    output_path: Path where the combined text file will be saved
  """
  try:
    input_path = Path(input_dir)
    if not input_path.exists() or not input_path.is_dir():
      raise ValueError(f"Invalid input directory: {input_dir}")
    
    pdf_files = list(input_path.glob("*.pdf"))
    if not pdf_files:
      logger.warning(f"No PDF files found in {input_dir}")
      return
    
    logger.info(f"Found {len(pdf_files)} PDF files in {input_dir}")
    
    # Create or truncate the output file
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
      os.makedirs(output_dir)
      
    with open(output_path, "w", encoding="utf-8") as f:
      f.write("# COMBINED PDF DOCUMENTS\n\n")
    
    # Process each PDF and append to the output file
    for pdf_file in pdf_files:
      try:
        logger.info(f"Processing {pdf_file.name}")
        parser = PDFParser(str(pdf_file))
        parsed_data = parser.parse_pdf()
        
        # Append this PDF's content to the output file
        with open(output_path, "a", encoding="utf-8") as f:
          f.write(f"\n\n{'=' * 50}\n")
          f.write(f"DOCUMENT: {pdf_file.name}\n")
          f.write(f"{'=' * 50}\n\n")
          
          f.write("--- DOCUMENT TEXT ---\n\n")
          f.write(parsed_data["text"])
          f.write("\n\n")
          
          f.write("--- DOCUMENT TABLES ---\n\n")
          for i, table in enumerate(parsed_data["tables"], 1):
            f.write(f"Table {i}:\n")
            f.write(table_to_text(table))
            f.write("\n\n")
        
      except Exception as e:
        logger.error(f"Error processing {pdf_file.name}: {str(e)}")
        
    logger.info(f"All documents processed and saved to {output_path}")
  except Exception as e:
    logger.error(f"Error processing directory: {str(e)}")


def main():
  """Main function to process all PDFs in a directory."""
  try:
    input_dir = "../dataset"  # Directory containing PDF files
    output_path = "../dataset/combined_dataset.txt"  # Output text file
    
    process_directory(input_dir, output_path)
    
  except Exception as e:
    logger.error(f"Error in main function: {str(e)}")


if __name__ == "__main__":
  main()
