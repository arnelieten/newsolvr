import json
from pathlib import Path

from google import genai
from google.genai import types

from config.config import GEMINI_API_KEY
from pipeline.utils.pipeline_dataclasses import ProblemReport


def fetch_prompt():
    path = Path(__file__).resolve().parent.parent / "prompts" / "problem_analyzer.md"
    return path.read_text(encoding="utf-8")


def analyze_article(article: str) -> dict:
    """Returns dict with problem_statement (str) and 14 score keys (int 0–5)."""
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        config=types.GenerateContentConfig(
            system_instruction=fetch_prompt(),
            max_output_tokens=1000,
            response_mime_type="application/json",
            response_schema=ProblemReport,
        ),
        contents=article,
    )
    return json.loads(response.text)
