import json
import time
from pathlib import Path

from google import genai
from google.genai import types
from pydantic import BaseModel

from config.config import GEMINI_API_KEY
from db_utils import close_db, connect_to_db, get_query, run_query

RATE_LIMIT_RPM = 15
RATE_LIMIT_RPD = 500


class Analysis(BaseModel):
    problem_verified: str
    problem_summary: str
    evidence_from_article: str
    startup_idea: str
    why_now: str
    early_adopters: str


def fetch_news_article():
    db_connection = connect_to_db()
    articles = get_query(
        db_connection,
        """SELECT uid,content_article from public.newsolvr
                          WHERE problem_verified IS NULL""",
    )
    close_db(db_connection)
    return articles


def get_llm_instructions():
    path = Path(__file__).parent / "llm_instructions.txt"
    return path.read_text(encoding="utf-8")


def llm_call(article):
    instructions = get_llm_instructions()

    client = genai.Client(api_key=GEMINI_API_KEY)

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        config=types.GenerateContentConfig(
            system_instruction=instructions,
            max_output_tokens=1000,
            response_mime_type="application/json",
            response_schema=list[Analysis],
        ),
        contents=article,
    )
    report = json.loads(response.text)[0]
    return report


def insert_report():
    db_connection = connect_to_db()
    articles = fetch_news_article()
    article_count = 0

    for uid, article in articles:
        if article_count >= RATE_LIMIT_RPD:
            break

        report = llm_call(article)
        run_query(
            db_connection,
            """UPDATE public.newsolvr SET 
                problem_verified = %s, 
                problem_summary = %s, 
                evidence_from_article = %s, 
                startup_idea = %s, 
                why_now = %s,
                early_adopters = %s
            WHERE uid = %s""",
            (
                report["problem_verified"],
                report["problem_summary"],
                report["evidence_from_article"],
                report["startup_idea"],
                report["why_now"],
                report["early_adopters"],
                uid,
            ),
        )
        article_count += 1
        print(f"News article {article_count} analysed")
        time.sleep(60 / RATE_LIMIT_RPM)
    close_db(db_connection)
