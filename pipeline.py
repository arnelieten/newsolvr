import time
from datetime import datetime, timedelta

from config.config import (
    LLM_RATE_LIMIT_RPD,
    LLM_RATE_LIMIT_RPM,
    NEWS_API_EXTRACTION_LAG_MINUTES,
    NEWS_API_EXTRACTION_WINDOW,
)
from utils.db_utils import close_db, connect_to_db, fetch_unanalyzed_articles, save_article_analysis
from utils.llm_utils import analyze_article
from utils.news_api_utils import (
    get_news_api_articles,
    save_news_api_articles,
    transform_news_api_articles,
)

# Specifically search for problems/issues in the news api.
NEWS_API_SEARCH_TOPIC = "problem OR issue NOT (no problem OR no issue)"


def run_article_extraction_pipeline(iterations: int = 24):
    """Fetch news articles from News API and persist to database. NEWS_API_EXTRACTION_LAG_MINUTES is needed becasue the free api only allows news from 24 hours back, the NEWS_API_EXTRACTION_WINDOW is a paramter that indicates the time period over which it retrieves all the articles (default 60 minutes). The iterations parameters decides how many windows of 60 minutes are run, default is 24 to capture news for whole day."""
    conn = connect_to_db()
    from_date = datetime.now() - timedelta(
        minutes=NEWS_API_EXTRACTION_LAG_MINUTES + NEWS_API_EXTRACTION_WINDOW
    )
    to_date = datetime.now() - timedelta(minutes=NEWS_API_EXTRACTION_LAG_MINUTES)

    for i in range(iterations):
        raw_news_articles = get_news_api_articles(NEWS_API_SEARCH_TOPIC, from_date, to_date)
        df_transformed_news_articles = transform_news_api_articles(raw_news_articles)
        save_news_api_articles(conn, df_transformed_news_articles)
        from_date -= timedelta(minutes=NEWS_API_EXTRACTION_WINDOW)
        to_date -= timedelta(minutes=NEWS_API_EXTRACTION_WINDOW)

    print("Pipeline complete: extract news articles from api.")
    close_db(conn)


def run_article_analysis_pipeline():
    """Fetch unanalyzed articles from the database, analyze each article with LLM, and save to database. This pipeline build on the extracted documents form News API scores them using Gemini LLMs."""
    conn = connect_to_db()
    articles = fetch_unanalyzed_articles(conn)
    count = 0

    for uid, content in articles:
        if count >= LLM_RATE_LIMIT_RPD:
            break
        report = analyze_article(content)
        save_article_analysis(conn, uid, report)
        count += 1
        print(f"Analysis complete for: article {count}")
        time.sleep(60 / LLM_RATE_LIMIT_RPM)

    print("Pipeline complete: analyze news articles with LLM.")
    close_db(conn)


def pipeline():
    """Pipeline that pulls news articles into database based on current_article_topic and performs LLM-based scoring for relevant problems."""
    run_article_extraction_pipeline()
    run_article_analysis_pipeline()


if __name__ == "__main__":
    pipeline()
