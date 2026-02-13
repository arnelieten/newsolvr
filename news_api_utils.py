from datetime import datetime, timedelta

import pandas as pd
import requests

from config.config import NEWS_API_KEY
from db_utils import close_db, connect_to_db, run_query

LAG_MINUTES = 1560  # 24h + 2h lag for free API
STEP_MINUTES = 60


def api_call(topic, from_date, to_date):
    base_url = "https://newsapi.org/v2/everything"

    headers = {"X-API-Key": NEWS_API_KEY}

    params = {"q": topic, "language": "en", "from": from_date, "to": to_date}

    response = requests.get(base_url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    print(f"Failed to connect with API {response.status_code}")
    return None


def transform_news_api(topic, from_date, to_date):
    news_data = api_call(topic, from_date, to_date)
    if news_data is None:
        return pd.DataFrame()

    df = pd.json_normalize(news_data, "articles")
    df = df[["title", "description", "content", "publishedAt", "url"]]
    df = df.dropna(subset=["title", "content"])
    df = df.drop_duplicates(subset="title")
    return df


def insert_news_api(df):
    db_connection = connect_to_db()
    for row in df.itertuples(index=False):
        run_query(
            db_connection,
            """INSERT INTO newsolvr
            (title_article, description_article, content_article, link_article, published_date)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (link_article) DO NOTHING""",
            (row.title, row.description, row.content, row.url, row.publishedAt),
        )
    close_db(db_connection)


def loop_news_api(current_topic, iterations, window):
    from_date = datetime.now() - timedelta(minutes=LAG_MINUTES + window * STEP_MINUTES)
    to_date = datetime.now() - timedelta(minutes=LAG_MINUTES)

    for i in range(iterations):
        df = transform_news_api(current_topic, from_date, to_date)
        insert_news_api(df)

        from_date -= timedelta(minutes=STEP_MINUTES)
        to_date -= timedelta(minutes=STEP_MINUTES)
        print(f"News articles batch {i + 1} inserted")
