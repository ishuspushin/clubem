
import os
import sys
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.config import Config
from app.agents.graph import ExtractionGraph

# Setup logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "process_uploads.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("process_uploads")

def main():
    # Load env with override to ensure new key is picked up
    load_dotenv(override=True)
    
    # Check API Key
    if not os.getenv("GOOGLE_API_KEY"):
        logger.error("GOOGLE_API_KEY not set in .env")
        return

    # Initialize Config and Graph
    try:
        config = Config.load_from_env()
        graph = ExtractionGraph(config)
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        return

    # Define groups
    upload_dir = Path("uploads")
    if not upload_dir.exists():
        logger.error("uploads directory not found")
        return

    # Map of platform -> files
    # We can group by some heuristics or hardcode for this specific request
    # The user said "remember there are two pdfs each for some platforms"
    
    groups = {
        "CaterCow": [
            "CaterCowCoversheetUnedited.pdf",
            "CaterCowLabelsUnedited.pdf"
        ],
        "ClubFeast": [
            "ClubFeastCoverUnedited.pdf",
            "ClubFeastLabelsUnedited.pdf"
        ],
        "Hungry": [
            "HungryCoverUnedited.pdf",
            "HungryLabelsUnedited.pdf"
        ],
        "Forkable": [
            "ForkableLabelsUnedited.pdf",
            "ForkableUneditedExcel.xlsx - Orders.pdf"
        ],
        "EzCater": ["EzCaterUnedited.pdf"],
        "Grubhub": ["GrubhuUnedited.pdf"],
        "Sharebite": ["SharebiteUnedited.pdf"]
    }

    # Create outputs directory
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    results_summary = {}

    for platform, filenames in groups.items():
        print(f"Processing {platform}...", flush=True)
        logger.info(f"\nProcessing {platform}...")

        # Check if output already exists to save quota
        output_file = output_dir / f"{platform}_output.json"
        if output_file.exists():
            try:
                with open(output_file, 'r') as f:
                    existing_data = json.load(f)
                if existing_data and isinstance(existing_data, list) and len(existing_data) > 0 and any(existing_data):
                    logger.info(f"Skipping {platform} - Output already exists and is valid. Preserving API quota.")
                    results_summary[platform] = {
                        "status": "skipped_existing",
                        "output_file": str(output_file)
                    }
                    continue
            except Exception as e:
                logger.warning(f"Existing output for {platform} is invalid, re-processing: {e}")
        
        # Verify files exist
        valid_files = []
        for fname in filenames:
            fpath = upload_dir / fname
            if fpath.exists():
                valid_files.append(str(fpath))
            else:
                logger.warning(f"File not found: {fname}")
        
        if not valid_files:
            logger.warning(f"No valid files for {platform}, skipping.")
            continue

        try:
            # Run Graph
            print(f"Running graph for {platform}...", flush=True)
            # Force platform since we know the grouping
            final_state = graph.run(pdf_files=valid_files, platform=platform.lower())
            print(f"Graph finished for {platform}", flush=True)

            
            # Analyze results
            extracted_data = final_state.get("extracted_data", [])
            errors = final_state.get("errors", [])
            
            logger.info(f"--- Results for {platform} ---")
            if errors:
                logger.error(f"Errors: {json.dumps(errors, indent=2)}")
            
            for i, data in enumerate(extracted_data):
                if not data:
                    logger.warning(f"Output {i+1}: Extraction failed")
                    continue
                    
                logger.info(f"Output {i+1}: Success")
                if "order_level" in data:
                    logger.info(f"  Client: {data['order_level'].get('business_client')}")
                    logger.info(f"  Guests: {data['order_level'].get('number_of_guests')}")
            
            # Save output to JSON file
            if extracted_data:
                output_file = output_dir / f"{platform}_output.json"
                with open(output_file, 'w') as f:
                    json.dump(extracted_data, f, indent=4)
                logger.info(f"Saved output to {output_file}")
            
            results_summary[platform] = {
                "success_count": len(extracted_data),
                "error_count": len(errors),
                "output_file": str(output_file) if extracted_data else None
            }

        except Exception as e:
            logger.error(f"Failed to process {platform}: {e}", exc_info=True)
            results_summary[platform] = {"error": str(e)}

    # Print Summary
    print("\n=== FINAL SUMMARY ===")
    print(json.dumps(results_summary, indent=2))

if __name__ == "__main__":
    main()
