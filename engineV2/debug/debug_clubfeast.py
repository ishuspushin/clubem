
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import Config
from app.agents.graph import ExtractionGraph

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("debug_clubfeast")

def main():
    load_dotenv(dotenv_path=project_root / '.env')
    config = Config.load_from_env()
    graph = ExtractionGraph(config)
    
    files = [
        str((project_root / "uploads/ClubFeastCoverUnedited.pdf").absolute()),
        str((project_root / "uploads/ClubFeastLabelsUnedited.pdf").absolute())
    ]
    
    print("Starting ClubFeast extraction...")
    try:
        final_state = graph.run(pdf_files=files)
        print("Extraction finished.")
        print("Keys in final state:", final_state.keys())
        if "extracted_data" in final_state:
            print("Extracted Data Count:", len(final_state["extracted_data"]))
        if "extraction_errors" in final_state:
            print("Errors:", final_state["extraction_errors"])
            
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
