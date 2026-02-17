import time
from datetime import datetime, timedelta

from config.config import (
    LLM_RATE_LIMIT_RPD,
    LLM_RATE_LIMIT_RPM,
    NEWS_API_EXTRACTION_LAG_MINUTES,
    NEWS_API_EXTRACTION_WINDOW,
    SCRAPE_DELAY_SECONDS,
)
from utils.db_utils import (
    close_db,
    connect_to_db,
    fetch_unanalyzed_articles,
    get_query,
    run_query,
    save_article_analysis,
    update_article_content,
)
from utils.llm_utils import analyze_article
from utils.news_api_utils import (
    extract_article_text,
    fetch_article_html,
    get_news_api_articles,
    save_news_api_articles,
    transform_news_api_articles,
)

# Specifically search for problems/issues in the news api.
NEWS_API_SEARCH_TOPIC = "technology OR tech OR software OR automation OR artificial intelligence"


def run_article_extraction_pipeline(iterations: int = 2):
    """Fetch news articles from News API and persist to database. NEWS_API_EXTRACTION_LAG_MINUTES is needed becasue the free api only allows news from 24 hours back, the NEWS_API_EXTRACTION_WINDOW is a paramter that indicates the time period over which it retrieves all the articles (default 60 minutes). The iterations parameters decides how many windows of 60 minutes are run, default is 24 to capture news for whole day."""
    conn = connect_to_db()
    window_delta = timedelta(minutes=NEWS_API_EXTRACTION_WINDOW)
    lag_delta = timedelta(minutes=NEWS_API_EXTRACTION_LAG_MINUTES)

    to_date = datetime.now() - lag_delta
    from_date = to_date - window_delta

    for n in range(iterations):
        raw_news_articles = get_news_api_articles(NEWS_API_SEARCH_TOPIC, from_date, to_date)
        df_transformed_news_articles = transform_news_api_articles(raw_news_articles)
        save_news_api_articles(conn, df_transformed_news_articles)

        from_date -= window_delta
        to_date -= window_delta

    print("Pipeline complete: extract news articles from api.")
    close_db(conn)


def run_html_extraction_pipeline():
    """Fetch HTML from link_article URLs for unanalyzed articles missing content; extract main text with trafilatura and update content_article."""
    conn = connect_to_db()
    rows = fetch_unanalyzed_articles(conn)
    count = 0
    for uid, link, content in rows:
        if content and content.strip():
            continue
        html = fetch_article_html(link)
        if html is None:
            continue
        text = extract_article_text(html)
        if text:
            update_article_content(conn, uid, text)
            count += 1
        time.sleep(SCRAPE_DELAY_SECONDS)
    print("Pipeline complete: extend content for articles in database.")
    close_db(conn)


def run_article_analysis_pipeline():
    """Fetch unanalyzed articles from the database, analyze each article with LLM, and save to database. This pipeline build on the extracted documents form News API scores them using Gemini LLMs."""
    conn = connect_to_db()
    articles = fetch_unanalyzed_articles(conn)
    count = 0

    for uid, _link, content in articles:
        if count >= LLM_RATE_LIMIT_RPD:
            break
        report = analyze_article(content)
        save_article_analysis(conn, uid, report)
        count += 1
        print(f"Analysis complete for: article {count}")
        time.sleep(60 / LLM_RATE_LIMIT_RPM)

    print("Pipeline complete: analyze news articles with Gemini.")
    close_db(conn)


def run_article_scoring_pipeline():
    """Set total_score = weighted average of the 14 rank columns for all analyzed articles."""
    conn = connect_to_db()
    try:
        rows = get_query(
            conn,
            """SELECT uid, meaningful_problem, pain_intensity, frequency, problem_size,
               market_growth, willingness_to_pay, target_customer_clarity, problem_awareness,
               competition, software_solution, ai_fit, speed_to_mvp, business_potential, time_relevancy
               FROM newsolvr WHERE problem_statement IS NOT NULL""",
        )
        weights = [1 / 14] * 14
        size_map = {"niche": 2, "global": 5}
        for row in rows:
            uid, *vals = row
            nums = [
                size_map.get((str(v).strip().lower() if v else ""), 3)
                if i == 3
                else (int(v) if v is not None else 0)
                for i, v in enumerate(vals)
            ]
            score = round(sum(w * n for w, n in zip(weights, nums)))
            run_query(conn, "UPDATE newsolvr SET total_score = ? WHERE uid = ?", (score, uid))
        print("Pipeline complete: score articles based on important params.")
    finally:
        close_db(conn)


def pipeline():
    """Pipeline that pulls news articles into database based on current_article_topic and performs LLM-based scoring for relevant problems."""
    # run_article_extraction_pipeline()
    # run_html_extraction_pipeline()
    # run_article_analysis_pipeline()
    run_article_scoring_pipeline()


if __name__ == "__main__":
    pipeline()
