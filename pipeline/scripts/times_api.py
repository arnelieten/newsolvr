import html as html_module
import re
from datetime import datetime, timedelta

import pandas as pd
import requests

from config.config import (
    API_EXTRACTION_LAG_MINUTES,
    API_EXTRACTION_WINDOW,
    TIMES_API_KEY,
)
from database import close_db, connect_to_db, run_query

BASE_URL = "https://api.nytimes.com/svc/search/v2/articlesearch.json"


def _html_to_plain(html: str) -> str:
    """Return plain text from HTML; empty string if missing/invalid."""
    if not html or not html.strip():
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    return html_module.unescape(text).strip()


def get_times_articles(topic: str, from_date: datetime, to_date: datetime) -> dict | None:
    """Fetch all pages of New York Times Article Search. Returns raw response JSON or None on failure."""
    if not TIMES_API_KEY:
        print("TIMES_API_KEY not set; skipping Times API.")
        return None
    begin_date = from_date.strftime("%Y%m%d")
    end_date = to_date.strftime("%Y%m%d")
    all_docs = []
    page = 0
    while page < 100:
        params = {
            "q": topic,
            "begin_date": begin_date,
            "end_date": end_date,
            "page": page,
            "sort": "newest",
            "api-key": TIMES_API_KEY,
        }
        resp = requests.get(BASE_URL, params=params)
        if resp.status_code != 200:
            print(f"Times API failed {resp.status_code}")
            return None
        data = resp.json()
        response = data.get("response", {})
        docs = response.get("docs", [])
        if not docs:
            break
        all_docs.extend(docs)
        if len(docs) < 10:
            break
        page += 1
    return {"response": {"docs": all_docs}} if all_docs else {"response": {"docs": []}}


def transform_times_articles(raw: dict | None) -> pd.DataFrame:
    """Build DataFrame with columns matching DB: title, content, url, published_date."""
    if not raw:
        return pd.DataFrame()
    docs = raw.get("response", {}).get("docs", [])
    if not docs:
        return pd.DataFrame()
    rows = []
    for doc in docs:
        headline = doc.get("headline") or {}
        title = headline.get("main") or headline.get("kicker") or ""
        url = doc.get("web_url") or ""
        if not title or not url:
            continue
        lead = _html_to_plain(doc.get("lead_paragraph") or "")
        snippet = _html_to_plain(doc.get("snippet") or "")
        content = lead if lead else snippet
        pub_date = doc.get("pub_date", "")
        if isinstance(pub_date, str) and "T" in pub_date:
            pub_date = pub_date.split("T")[0]
        rows.append(
            {
                "title": title,
                "content": content,
                "url": url,
                "published_date": pub_date,
            }
        )
    df = pd.DataFrame(rows).drop_duplicates(subset="url")
    return df


def save_times_articles(conn, df: pd.DataFrame) -> None:
    """Insert Times rows into newsolvr. Caller manages connection."""
    for row in df.itertuples(index=False):
        run_query(
            conn,
            """INSERT INTO newsolvr
            (title_article, content_article, link_article, published_date)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (link_article) DO NOTHING""",
            (row.title, row.content, row.url, row.published_date),
        )


def times_api_extraction_pipeline(search_topic: str, iterations: int = 24):
    """Fetch New York Times articles and persist to database. Reuses API_EXTRACTION_WINDOW and LAG from config. iterations defaults to 24 for full-day coverage."""
    conn = connect_to_db()
    window_delta = timedelta(minutes=API_EXTRACTION_WINDOW)
    lag_delta = timedelta(minutes=API_EXTRACTION_LAG_MINUTES)
    to_date = datetime.now() - lag_delta
    from_date = to_date - window_delta
    for _ in range(iterations):
        raw = get_times_articles(search_topic, from_date, to_date)
        df = transform_times_articles(raw)
        save_times_articles(conn, df)
        from_date -= window_delta
        to_date -= window_delta
    print("Pipeline complete: extract Times articles from api.")
    close_db(conn)
