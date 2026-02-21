import html as html_module
import re
from datetime import datetime, timedelta

import pandas as pd
import requests

from config.config import API_EXTRACTION_LAG_MINUTES, API_EXTRACTION_WINDOW, GUARDIAN_API_KEY
from database import close_db, connect_to_db, run_query

BASE_URL = "https://content.guardianapis.com/search"


def _html_to_plain(html: str) -> str:
    """Return plain text from HTML; empty string if missing/invalid."""
    if not html or not html.strip():
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    return html_module.unescape(text).strip()


def get_guardian_articles(topic: str, from_date, to_date) -> list | None:
    """Fetch all pages of Guardian search. Returns list of result dicts or None on failure."""
    params = {
        "q": topic,
        "from-date": from_date.strftime("%Y-%m-%d"),
        "to-date": to_date.strftime("%Y-%m-%d"),
        "order-by": "newest",
        "show-fields": "standfirst,body",
        "page-size": 50,
        "api-key": GUARDIAN_API_KEY,
    }
    results = []
    page = 1
    while True:
        params["page"] = page
        resp = requests.get(BASE_URL, params=params)
        if resp.status_code != 200:
            print(f"Guardian API failed {resp.status_code}")
            return None
        data = resp.json()
        r = data.get("response", {})
        if r.get("status") != "ok":
            return None
        results.extend(r.get("results", []))
        if page >= r.get("pages", 1):
            break
        page += 1
    return results


def transform_guardian_articles(raw: list | None) -> pd.DataFrame:
    """Build DataFrame with columns matching DB: title, content, link, published_date."""
    if not raw:
        return pd.DataFrame()
    rows = []
    for r in raw:
        title, url = r.get("webTitle"), r.get("webUrl")
        if not title or not url:
            continue
        fields = r.get("fields") or {}
        body_html = fields.get("body", "") or ""
        rows.append(
            {
                "title": title,
                "content": _html_to_plain(body_html),
                "url": url,
                "published_date": r.get("webPublicationDate", ""),
            }
        )
    df = pd.DataFrame(rows).drop_duplicates(subset="url")
    return df


def save_guardian_articles(conn, df: pd.DataFrame) -> None:
    """Insert Guardian rows into newsolvr. Caller manages connection."""
    for row in df.itertuples(index=False):
        run_query(
            conn,
            """INSERT INTO newsolvr
            (title_article, content_article, link_article, published_date)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (link_article) DO NOTHING""",
            (row.title, row.content, row.url, row.published_date),
        )


def guardian_api_extraction_pipeline(search_topic: str, iterations: int = 24):
    """Fetch Guardian articles and persist to database. Reuses API_EXTRACTION_WINDOW and LAG from config. iterations defaults to 24 for full-day coverage."""
    conn = connect_to_db()
    window_delta = timedelta(minutes=API_EXTRACTION_WINDOW)
    lag_delta = timedelta(minutes=API_EXTRACTION_LAG_MINUTES)
    to_date = datetime.now() - lag_delta
    from_date = to_date - window_delta
    for _ in range(iterations):
        raw = get_guardian_articles(search_topic, from_date, to_date)
        df = transform_guardian_articles(raw)
        save_guardian_articles(conn, df)
        from_date -= window_delta
        to_date -= window_delta
    print("Pipeline complete: extract Guardian articles from api.")
    close_db(conn)
