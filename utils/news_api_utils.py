import pandas as pd
import requests

from config.config import NEWS_API_KEY
from utils.db_utils import run_query


def get_news_api_articles(topic, from_date, to_date):
    """Fetch raw JSON from News API. Returns None on failure."""
    base_url = "https://newsapi.org/v2/everything"
    headers = {"X-API-Key": NEWS_API_KEY}
    params = {"q": topic, "language": "en", "from": from_date, "to": to_date}
    response = requests.get(base_url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    print(f"Failed to connect with API {response.status_code}")
    return None


def transform_news_api_articles(raw_news_articles):
    """Turn raw API response into a cleaned DataFrame. Pass None for empty df."""
    if raw_news_articles is None:
        return pd.DataFrame()
    df = pd.json_normalize(raw_news_articles, "articles")
    df = df[["title", "description", "content", "publishedAt", "url"]]
    df = df.dropna(subset=["title", "content"])
    df = df.drop_duplicates(subset="title")
    return df


def save_news_api_articles(db_connection, df):
    """Insert news API rows into newsolvr. Caller manages connection lifecycle."""
    for row in df.itertuples(index=False):
        run_query(
            db_connection,
            """INSERT INTO newsolvr
            (title_article, description_article, content_article, link_article, published_date)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (link_article) DO NOTHING""",
            (row.title, row.description, row.content, row.url, row.publishedAt),
        )
