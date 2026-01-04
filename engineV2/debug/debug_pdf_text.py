
import sys
from pathlib import Path
import logging

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.pdf_processor import PDFProcessor

logging.basicConfig(level=logging.INFO)

def main():
    processor = PDFProcessor()
    files_to_check = [
        "uploads/CaterCowLabelsUnedited.pdf",
        "uploads/ClubFeastCoverUnedited.pdf",
        "uploads/ClubFeastLabelsUnedited.pdf",
        "uploads/HungryLabelsUnedited.pdf",
        "uploads/ForkableLabelsUnedited.pdf",
        "uploads/ForkableUneditedExcel.xlsx - Orders.pdf"
    ]
    
    for fname in files_to_check:
        print(f"\n\n=== {fname} ===")
        try:
            fpath = project_root / fname
            text = processor.extract_text(str(fpath))
            print(text[:1000])
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
