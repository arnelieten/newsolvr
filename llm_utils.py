import json
from google import genai
from google.genai import types
from pydantic import BaseModel
from db_utils import connect_to_db, close_query, get_query, run_query

def fetch_news_article():
     dcb = connect_to_db()
     articles = get_query(dcb, """SELECT content_article from public.newsolvr""")
     close_query(dcb)
     return articles

class Analysis(BaseModel):
    problem_verified: str
    problem_summary: str
    target_market: str
    startup_idea: str
    business_model: str

def llm_call():
    with open("llm_api_credentials.json", "r") as f:
            headers = json.load(f)
            API_KEY = headers['api-key']
    
    articles = fetch_news_article()
    article = articles[9]

    client = genai.Client(api_key=API_KEY)

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        config=types.GenerateContentConfig(
            system_instruction = "You are experienced serial entrepreneur that is doing market research, for this you scan the internet for relevant problems. The input you are getting is a newsarticle and I am asking you for your perspective. Question 1: is this really a problem where someone could build a startup around, be strict and put yes or no in 'problem_verified' of the response schema. Question 2: if it is a real problem summarize the problem, if not a real problem just put N/A 'problem_verified' of the response schema. Question 3: How big is the target market for this problem in euros, if you do not know put 0 in 'target_market' of the response schema. Question 4: Be creative and invent a startup idea and put a short description in 'startup_idea' of the response schema. Question 5: based on your invented startup idea, is it B2C or B2B and put that answer in 'business_model' of the response schema.",
            max_output_tokens = 1000,
            response_mime_type = "application/json",
            response_schema= list[Analysis]),
        contents=article)
    report = json.loads(response.text)
    report = report[0]
    return report

def insert_report():
    dcb = connect_to_db()
    report = llm_call()
    run_query(dcb, 
        """INSERT INTO public.newsolvr 
        (problem_verified, problem_summary, target_market, startup_idea, business_model) 
        VALUES (%s, %s, %s, %s, %s)""",
        (report["problem_verified"], report["problem_summary"], report["target_market"], report["startup_idea"], report["business_model"]))
    close_query(dcb)
    print('done')

insert_report()