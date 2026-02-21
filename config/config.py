import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

_DEFAULT_FETCH_HTML_HEADERS = {
    "User-Agent": "newsolvr/1.0 (news aggregation; +https://github.com/newsolvr)"
}

# Database
DB_PATH = os.getenv("DB_PATH")

# APIs
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GUARDIAN_API_KEY = os.getenv("GUARDIAN_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Internal logic
LLM_RATE_LIMIT_RPM = int(os.getenv("LLM_RATE_LIMIT_RPM"))
LLM_RATE_LIMIT_RPD = int(os.getenv("LLM_RATE_LIMIT_RPD"))
API_EXTRACTION_LAG_MINUTES = int(os.getenv("API_EXTRACTION_LAG_MINUTES"))
API_EXTRACTION_WINDOW = int(os.getenv("API_EXTRACTION_WINDOW"))

# Web scraping
FETCH_HTML_TIMEOUT = int(os.getenv("FETCH_HTML_TIMEOUT", "10"))
_headers_env = os.getenv("FETCH_HTML_HEADERS")
FETCH_HTML_HEADERS = json.loads(_headers_env) if _headers_env else _DEFAULT_FETCH_HTML_HEADERS
SCRAPE_DELAY_SECONDS = int(os.getenv("SCRAPE_DELAY_SECONDS", "1"))
