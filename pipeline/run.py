import time

from config.config import LLM_RATE_LIMIT_RPD, LLM_RATE_LIMIT_RPM, SCRAPE_DELAY_SECONDS
from database import (
    close_db,
    connect_to_db,
    fetch_unanalyzed_articles,
    get_query,
    run_query,
    save_article_analysis,
    update_article_content,
)
from pipeline.utils.guardian_api_utils import guardian_api_extraction_pipeline
from pipeline.utils.llm_utils import analyze_article
from pipeline.utils.news_api_utils import (
    extract_article_text,
    fetch_article_html,
    news_api_extraction_pipeline,
)
from pipeline.utils.pipeline_dataclasses import SCORE_COLUMNS
from pipeline.utils.timeliness_utils import timeliness_score
from pipeline.utils.times_api_utils import times_api_extraction_pipeline

SEARCH_TOPIC = "technology OR tech OR software OR automation OR artificial intelligence"


def run_article_extraction_pipeline(search_topic: str = SEARCH_TOPIC):
    news_api_extraction_pipeline(search_topic, iterations=1)
    guardian_api_extraction_pipeline(search_topic, iterations=1)
    times_api_extraction_pipeline(search_topic, iterations=1)


def run_deduplication_pipeline():
    """Remove duplicate articles (same title_article) in the last 3 days, keeping the earliest by published_date."""
    conn = connect_to_db()
    run_query(
        conn,
        """DELETE FROM newsolvr WHERE date(published_date) >= date('now', '-3 days') AND uid IN (
            SELECT uid FROM (
                SELECT uid, ROW_NUMBER() OVER (PARTITION BY title_article ORDER BY published_date ASC) AS rn
                FROM newsolvr WHERE date(published_date) >= date('now', '-3 days')
            ) WHERE rn > 1
        )""",
    )
    print("Pipeline complete: deduplication based on article titles.")
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
            f"SELECT uid, {cols}, published_date FROM newsolvr WHERE problem_statement IS NOT NULL",
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
            published_date = row[15]

            score = 0.0
            score += meaningful_problem * 5
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
            score += timeliness_score(published_date) * 1
            # total weights = 25

            final_score = round((score / (25 * 5)) * 100)
            run_query(conn, "UPDATE newsolvr SET total_score = ? WHERE uid = ?", (final_score, uid))
        print("Pipeline complete: score articles.")
    finally:
        close_db(conn)


def pipeline():
    """Pipeline that pulls news articles into database based on current_article_topic and performs LLM-based scoring for relevant problems."""
    # run_article_extraction_pipeline()
    run_deduplication_pipeline()
    # run_html_extraction_pipeline()
    # run_article_analysis_pipeline()
    run_article_scoring_pipeline()
