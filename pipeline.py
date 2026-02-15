import time

from utils.db_utils import close_db, connect_to_db, fetch_unanalyzed_articles, save_article_analysis
from utils.llm_utils import analyze_article
from utils.news_api_utils import loop_news_api

LLM_RATE_LIMIT_RPM = 20
LLM_RATE_LIMIT_RPD = 200

current_article_topic = "problem OR issue NOT (no problem OR no issue)"


def run_article_analysis_pipeline():
    """Fetch unanalyzed articles from the database, analyze each article with LLM, and save to database."""
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

    close_db(conn)


def pipeline():
    """Pipeline that pulls news articles into database based on current_article_topic and performs LLM-based scoring for relevant problems."""
    loop_news_api(current_article_topic, 4, 1)
    run_article_analysis_pipeline()


if __name__ == "__main__":
    pipeline()
