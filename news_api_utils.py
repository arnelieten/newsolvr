import requests
import json
import pandas as pd
from db_utils import connect_to_db, run_query, close_query
from datetime import datetime, timedelta

def api_call(topic, from_date, to_date):
    base_url = "https://newsapi.org/v2/everything"

    with open("news_api_credentials.json", "r") as f:
        headers = json.load(f)

    params = {
        "q" : topic,
        "language" : "en",
        "from" : from_date,
        "to" : to_date

    }

    response = requests.get(base_url, headers=headers, params=params)

    if response.status_code == 200:
        news_data = response.json()
        return news_data
    else:
        print(f"Failed to connect with API {response.status_code}")


def transform_news_api(topic, from_date, to_date):
    news_data = api_call(topic, from_date, to_date)

    df = pd.json_normalize(news_data, 'articles')
    df = df[['title', 'description', 'content', 'publishedAt', 'url']]
    df = df.dropna(subset=['title', 'content'])
    df = df.drop_duplicates(subset='title')
    return df

def insert_news_api(df):
    dcb = connect_to_db()
    for row in df.itertuples(index=False):
        run_query(dcb, 
            """INSERT INTO public.newsolvr 
            (title_article, description_article, content_article, link_article, published_date) 
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (link_article) DO NOTHING""", 
            (row.title, row.description, row.content, row.url, row.publishedAt))
    close_query(dcb)

def loop_news_api(current_topic,iterations):
    # implement solution to not error if no articles found!!
    from_date = datetime.now() - timedelta(minutes=1620)
    to_date = datetime.now() - timedelta(minutes=1560)
    
    for i in range(iterations): #100 free api calls per day
        df = transform_news_api(current_topic, from_date, to_date)
        insert_news_api(df)

        from_date -= timedelta(minutes=60)
        to_date -= timedelta(minutes=60)
        print(f"News articles batch {i+1} inserted")