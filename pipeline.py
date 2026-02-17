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
from utils.pipeline_dataclasses import SCORE_COLUMNS

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


def run_article_scoring_pipeline(params=SCORE_COLUMNS):
    """Score each article on 100: weighted score based on different subscores in database."""

    cols = ", ".join(params)
    conn = connect_to_db()
    try:
        rows = get_query(
            conn,
            f"SELECT uid, {cols} FROM newsolvr WHERE problem_statement IS NOT NULL",
        )
        for row in rows:
            uid = row[0]
            meaningful_problem = int(row[1])
            pain_intensity = int(row[2])
            frequency = int(row[3])
            market_growth = int(row[5])
            willingness_to_pay = int(row[6])
            target_customer_clarity = int(row[7])
            problem_awareness = int(row[8])
            competition = int(row[9])
            software_solution = int(row[10])
            ai_fit = int(row[11])
            speed_to_mvp = int(row[12])
            business_potential = int(row[13])
            time_relevancy = int(row[14])

            score = 0.0
            score += meaningful_problem * 3
            score += pain_intensity * 2
            score += frequency * 1
            score += market_growth * 3
            score += willingness_to_pay * 1
            score += target_customer_clarity * 1
            score += problem_awareness * 1
            score += competition * 1
            score += software_solution * 2
            score += ai_fit * 2
            score += speed_to_mvp * 3
            score += business_potential * 1
            score += time_relevancy * 1
            # current total weights = 22

            final_score = round((score / (22 * 5)) * 100)
            run_query(conn, "UPDATE newsolvr SET total_score = ? WHERE uid = ?", (final_score, uid))
        print("Pipeline complete: score articles.")
    finally:
        close_db(conn)


def pipeline():
    """Pipeline that pulls news articles into database based on current_article_topic and performs LLM-based scoring for relevant problems."""
    # run_article_extraction_pipeline()
    run_html_extraction_pipeline()
    run_article_analysis_pipeline()
    run_article_scoring_pipeline()


if __name__ == "__main__":
    pipeline()
