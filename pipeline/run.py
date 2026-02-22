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
from pipeline.scripts.guardian_api import guardian_api_extraction_pipeline
from pipeline.scripts.llm_functions import analyze_article
from pipeline.scripts.news_api import (
    extract_article_text,
    fetch_article_html,
    news_api_extraction_pipeline,
)
from pipeline.scripts.pipeline_dataclasses import NUMERIC_SCORE_COLUMNS
from pipeline.scripts.timeliness_functions import timeliness_score
from pipeline.scripts.times_api import times_api_extraction_pipeline
from utils.error_handling import handle_pipeline_errors

SEARCH_TOPIC = "technology OR tech OR software OR automation OR artificial intelligence"


@handle_pipeline_errors
def run_article_extraction_pipeline(search_topic: str = SEARCH_TOPIC):
    news_api_extraction_pipeline(search_topic, iterations=1)
    guardian_api_extraction_pipeline(search_topic, iterations=1)
    times_api_extraction_pipeline(search_topic, iterations=1)


@handle_pipeline_errors
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


@handle_pipeline_errors
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


@handle_pipeline_errors
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


@handle_pipeline_errors
def run_article_scoring_pipeline(params=None):
    """Score each article on 100: weighted score based on different subscores in database."""
    if params is None:
        params = NUMERIC_SCORE_COLUMNS

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
            market_growth = int(row[4])
            willingness_to_pay = int(row[5])
            target_customer_clarity = int(row[6])
            problem_awareness = int(row[7])
            competition = int(row[8])
            software_solution = int(row[9])
            ai_fit = int(row[10])
            speed_to_mvp = int(row[11])
            business_potential = int(row[12])
            time_relevancy = int(row[13])
            published_date = row[14]

            score_without_timeliness = 0.0
            score_without_timeliness += meaningful_problem * 5
            score_without_timeliness += pain_intensity * 2
            score_without_timeliness += frequency * 1
            score_without_timeliness += market_growth * 3
            score_without_timeliness += willingness_to_pay * 1
            score_without_timeliness += target_customer_clarity * 1
            score_without_timeliness += problem_awareness * 1
            score_without_timeliness += competition * 1
            score_without_timeliness += software_solution * 2
            score_without_timeliness += ai_fit * 2
            score_without_timeliness += speed_to_mvp * 3
            score_without_timeliness += business_potential * 1
            score_without_timeliness += time_relevancy * 1
            # total weights without timeliness = 24

            score = score_without_timeliness * timeliness_score(published_date)

            original_score = round((score_without_timeliness / (24 * 5)) * 100)
            final_score = round((score / (24 * 5)) * 100)
            run_query(
                conn,
                "UPDATE newsolvr SET original_score = ?, total_score = ? WHERE uid = ?",
                (original_score, final_score, uid),
            )
        print("Pipeline complete: score articles.")
    finally:
        close_db(conn)


@handle_pipeline_errors
def run_database_cleanup_pipeline():
    """Remove all rows with original_score < 85 so the database keeps only high-value problems."""
    conn = connect_to_db()
    try:
        run_query(
            conn,
            "DELETE FROM newsolvr WHERE original_score IS NOT NULL AND original_score < 85",
        )
        print("Pipeline complete: database cleanup.")
    finally:
        close_db(conn)


def pipeline():
    """Pipeline that pulls news articles into database based on current_article_topic and performs LLM-based scoring for relevant problems."""
    run_article_extraction_pipeline()
    run_deduplication_pipeline()
    run_html_extraction_pipeline()
    run_article_analysis_pipeline()
    run_article_scoring_pipeline()
    run_database_cleanup_pipeline()
