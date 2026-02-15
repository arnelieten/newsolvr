import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

# Database
DB_PATH = os.getenv("DB_PATH")

# APIs
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Internal logic
LLM_RATE_LIMIT_RPM = int(os.getenv("LLM_RATE_LIMIT_RPM"))
LLM_RATE_LIMIT_RPD = int(os.getenv("LLM_RATE_LIMIT_RPD"))
NEWS_API_EXTRACTION_LAG_MINUTES = int(os.getenv("NEWS_API_EXTRACTION_LAG_MINUTES"))
NEWS_API_EXTRACTION_WINDOW = int(os.getenv("NEWS_API_EXTRACTION_WINDOW"))
