import json
import time
from google import genai
from google.genai import types
from pydantic import BaseModel
from db_utils import connect_to_db, close_query, get_query, run_query

RATE_LIMIT_RPM = 15
RATE_LIMIT_RPD = 500
class Analysis(BaseModel):
    problem_verified: str
    problem_summary: str
    target_market: str
    startup_idea: str
    business_model: str

def fetch_news_article():
     dcb = connect_to_db()
     articles = get_query(dcb, """SELECT uid,content_article from public.newsolvr""")
     close_query(dcb)
     return articles

def llm_call(article):
    with open("llm_api_credentials.json", "r") as f:
            headers = json.load(f)
            API_KEY = headers['api-key']

    client = genai.Client(api_key=API_KEY)

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        config=types.GenerateContentConfig(
            system_instruction = "You are experienced serial entrepreneur that is doing market research, for this you scan the internet for relevant problems. The input you are getting is a newsarticle and I am asking you for your perspective. Question 1: is this really a problem where someone could build a startup around, be strict and put yes or no in 'problem_verified' of the response schema. Question 2: if it is a real problem summarize the problem, if not a real problem just put N/A 'problem_verified' of the response schema. Question 3: How big is the target market for this problem in euros, if you do not know put 0 in 'target_market' of the response schema. Question 4: Be creative and invent a startup idea and put a short description in 'startup_idea' of the response schema. Question 5: based on your invented startup idea, is it B2C or B2B and put that answer in 'business_model' of the response schema.",
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
                target_market = %s, 
                startup_idea = %s, 
                business_model = %s 
            WHERE uid = %s""",
            (report["problem_verified"], report["problem_summary"], report["target_market"], report["startup_idea"], report["business_model"], uid))
        article_count += 1
        print(f'News article {article_count} analysed')
        time.sleep(60/RATE_LIMIT_RPM)
    close_query(dcb)