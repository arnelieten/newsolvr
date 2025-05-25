import json
from google import genai
from db_utils import connect_to_db, close_query, get_query

def fetch_news_article():
     dcb = connect_to_db()
     articles = get_query(dcb, """SELECT content_article from public.newsolvr""")
     close_query(dcb)
     return articles

def llm_call():
    with open("llm_api_credentials.json", "r") as f:
            headers = json.load(f)
            API_KEY = headers['api-key']
    
    articles = fetch_news_article()
    article = articles[1]

    client = genai.Client(api_key=API_KEY)

    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=article
    )
    print(response.text)

llm_call()