import json
import time
from dotenv import dotenv_values
from google import genai
from google.genai import types
from pydantic import BaseModel
from db_utils import connect_to_db, close_query, get_query, run_query

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
     dcb = connect_to_db()
     articles = get_query(dcb, """SELECT uid,content_article from public.newsolvr
                          WHERE problem_verified IS NULL""")
     close_query(dcb)
     return articles

def open_llm_instructions():
    with open("llm_instructions.txt", "r", encoding="utf-8") as f:
        instructions = f.read()
    return instructions

def llm_call(article):
    config = dotenv_values(".env")
    instructions = open_llm_instructions()
    GEMINI_API_KEY = config["GEMINI_API_KEY"]

    client = genai.Client(api_key=GEMINI_API_KEY)

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        config=types.GenerateContentConfig(
            system_instruction = instructions,
            max_output_tokens = 1000,
            response_mime_type = "application/json",
            response_schema= list[Analysis]),
        contents=article)
    report = json.loads(response.text)[0]
    return report

def insert_report():
    dcb = connect_to_db()
    articles=fetch_news_article()
    article_count = 0

    for uid,article in articles:
        if article_count > RATE_LIMIT_RPD:
            break

        report = llm_call(article)  
        run_query(dcb, 
            """UPDATE public.newsolvr SET 
                problem_verified = %s, 
                problem_summary = %s, 
                evidence_from_article = %s, 
                startup_idea = %s, 
                why_now = %s,
                early_adopters = %s
            WHERE uid = %s""",
            (report["problem_verified"], report["problem_summary"], report["evidence_from_article"], report["startup_idea"], report["why_now"], report["early_adopters"], uid))
        article_count += 1
        print(f'News article {article_count} analysed')
        time.sleep(60/RATE_LIMIT_RPM)
    close_query(dcb)