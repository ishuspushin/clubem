import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.core.pdf_processor import PDFProcessor

# Setup
logging.basicConfig(level=logging.INFO)
load_dotenv(dotenv_path=project_root / '.env', override=True)
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel(
    "gemini-2.0-flash",
    generation_config={
        "response_mime_type": "application/json",
        "temperature": 0.1
    }
)

# Extract Text
pdf_processor = PDFProcessor()
file_path = project_root / "uploads/ForkableLabelsUnedited.pdf"

try:
    print(f"Extracting {file_path}...")
    text = pdf_processor.extract_text(file_path)
    print(f"Extracted {len(text)} chars.")
    
    # Use the actual prompt template if possible, or a strong JSON prompt
    prompt = f"""
    You are an expert PDF data extractor. Extract the following information from this Forkable group order PDF:
    
    Extract:
    - Business Client
    - Group Order Number
    - Guest Names and their Items
    
    Return ONLY valid JSON.
    
    **PDF CONTENT:**
    {text}
    """
    
    print("Sending to Gemini...")
    response = model.generate_content(prompt)
    print("Response object received.")
    
    if response.prompt_feedback:
        print(f"Prompt feedback: {response.prompt_feedback}")

    if not response.parts:
        print("No parts in response.")
        if response.candidates:
             print(f"Finish reason: {response.candidates[0].finish_reason}")
             print(f"Safety ratings: {response.candidates[0].safety_ratings}")
    
    print("Text length:", len(response.text))
    print("Response text start:")
    print(response.text[:500]) 
    print("Response text end:")
    print(response.text[-500:])
    
except Exception as e:
    print(f"Error: {e}")
