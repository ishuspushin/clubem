
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# Load .env from project root
project_root = Path(__file__).parent.parent
load_dotenv(dotenv_path=project_root / '.env', override=True)
api_key = os.getenv("GOOGLE_API_KEY")
print(f"API Key present: {bool(api_key)}")

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    print("Model initialized. Sending request...")
    response = model.generate_content("Hello, are you working?")
    print("Response received.")
    print(response.text)
except Exception as e:
    print(f"Error: {e}")
