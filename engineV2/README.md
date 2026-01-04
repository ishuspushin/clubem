# 🍽️ Group Order Extraction System

AI-powered PDF extraction system for restaurant group orders using **Google Gemini 2.0 Flash** / **OpenAI GPT-4o** and **LangGraph**.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ Features

- 🤖 **AI-Powered Extraction** - Leverages Google Gemini 2.0 Flash or OpenAI GPT-4o for intelligent PDF parsing
- 📄 **Multi-Platform Support** - Handles 7 different food ordering platforms
- 🔄 **Human-in-the-Loop** - Optional review workflow for quality assurance
- 🔁 **Smart Retry Logic** - Automatic retry with exponential backoff
- ✅ **Data Validation** - Pydantic schemas ensure data integrity
- 🌐 **RESTful API** - Clean, documented API endpoints
- 🐳 **Docker Ready** - Complete containerization support
- 📊 **Structured Logging** - Comprehensive logging and monitoring
- 🎯 **Type-Safe** - Full type hints throughout the codebase
- 🔌 **Provider Agnostic** - Easily switch between Google Gemini and OpenAI

---

## 🍔 Supported Platforms

| Platform      | Status | Format                    |
| ------------- | ------ | ------------------------- |
| **Sharebite** | ✅     | Cover + Individual Orders |
| **EzCater**   | ✅     | Bulk Orders               |
| **Grubhub**   | ✅     | Team Orders               |
| **CaterCow**  | ✅     | Cover + Labels            |
| **ClubFeast** | ✅     | Cover + Labels            |
| **Hungry**    | ✅     | Food Partner Form         |
| **Forkable**  | ✅     | Standard Orders           |

---

## 📂 Project Structure

- `app/` - Application source code
  - `agents/` - LangGraph workflows and nodes
  - `core/` - Core configuration and utilities
  - `models/` - Pydantic data models
- `logs/` - Execution logs (e.g., `process_uploads.log`)
- `debug/` - Debugging scripts and utilities
- `outputs/` - Generated JSON output files
- `uploads/` - Input PDF files

## 🛠️ Debugging

The `debug/` folder contains scripts to test specific components. These scripts automatically handle path resolution to work from the `debug/` directory.

- `debug_gemini.py`: Verify API key and Gemini model connection
- `debug_pdf_text.py`: Test PDF text extraction
- `debug_forkable.py`: Test extraction for specific platforms (e.g., Forkable)
- `list_models.py`: List available Gemini models

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Google Gemini API Key** ([Get one here](https://makersuite.google.com/app/apikey))
- **Git**

### Installation (Local)

```bash
# 1. Clone the repository
#git clone https://github.com/yourusername/group-order-extraction.git
#cd group-order-extraction

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and set your preferred LLM_PROVIDER ('gemini' or 'openai')
# Add your GOOGLE_API_KEY or OPENAI_API_KEY

# 5. Run batch processing
python process_uploads.py

# Or start the API server
python run.py
```
