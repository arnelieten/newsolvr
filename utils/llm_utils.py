import json
import time
from pathlib import Path

from google import genai
from google.genai import types
from pydantic import BaseModel

from config.config import GEMINI_API_KEY
from utils.db_utils import close_db, connect_to_db, get_query, run_query

RATE_LIMIT_RPM = 15
RATE_LIMIT_RPD = 500


class ProblemReport(BaseModel):
    """Matches problem_analyzer.md: one summary + 14 scores (1–5)."""

    problem_statement: str
    meaningful_problem: int
    pain_intensity: int
    frequency: int
    problem_size: int
    market_growth: int
    willingness_to_pay: int
    target_customer_clarity: int
    problem_awareness: int
    differentiation_potential: int
    software_solution: int
    ai_fit: int
    speed_to_mvp: int
    business_potential: int
    time_relevancy: int


def fetch_prompt():
    path = Path(__file__).parent.parent / "prompts" / "problem_analyzer.md"
    return path.read_text(encoding="utf-8")


def fetch_unanalyzed_articles():
    conn = connect_to_db()
    rows = get_query(
        conn, "SELECT uid, content_article FROM newsolvr WHERE problem_statement IS NULL"
    )
    close_db(conn)
    return rows


def analyze_article(article: str) -> dict:
    """Returns dict with problem_statement (str) and 14 score keys (int 1–5)."""
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


def generate_report():
    conn = connect_to_db()
    articles = fetch_unanalyzed_articles()
    count = 0

    for uid, content in articles:
        if count >= RATE_LIMIT_RPD:
            break
        report = analyze_article(content)

        run_query(
            conn,
            """UPDATE newsolvr SET
                problem_statement = ?, meaningful_problem = ?, pain_intensity = ?,
                frequency = ?, problem_size = ?, market_growth = ?, willingness_to_pay = ?,
                target_customer_clarity = ?, problem_awareness = ?, competition = ?,
                software_solution = ?, ai_fit = ?, speed_to_mvp = ?,
                business_potential = ?, time_relevancy = ?
            WHERE uid = ?""",
            (
                report["problem_statement"],
                report["meaningful_problem"],
                report["pain_intensity"],
                report["frequency"],
                report["problem_size"],
                report["market_growth"],
                report["willingness_to_pay"],
                report["target_customer_clarity"],
                report["problem_awareness"],
                report["differentiation_potential"],
                report["software_solution"],
                report["ai_fit"],
                report["speed_to_mvp"],
                report["business_potential"],
                report["time_relevancy"],
                uid,
            ),
        )
        count += 1
        print(f"Analysis complete for: article {count}")
        time.sleep(60 / RATE_LIMIT_RPM)

    close_db(conn)
