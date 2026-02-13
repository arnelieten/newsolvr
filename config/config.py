import os

from dotenv import load_dotenv

load_dotenv()

# Database
DB_PATH = os.getenv("DB_PATH")

# APIs
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
