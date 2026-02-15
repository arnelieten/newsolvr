import sqlite3
import threading

from config.config import DB_PATH

INIT_SQL = """
CREATE TABLE IF NOT EXISTS newsolvr (
    uid INTEGER PRIMARY KEY AUTOINCREMENT,
    title_article TEXT,
    description_article TEXT,
    content_article TEXT,
    link_article TEXT UNIQUE,
    published_date TEXT,
    problem_statement TEXT,
    meaningful_problem INTEGER,
    pain_intensity INTEGER,
    frequency INTEGER,
    problem_size TEXT,
    market_growth INTEGER,
    willingness_to_pay INTEGER,
    target_customer_clarity INTEGER,
    problem_awareness INTEGER,
    competition INTEGER,
    software_solution INTEGER,
    ai_fit INTEGER,
    speed_to_mvp INTEGER,
    business_potential INTEGER,
    time_relevancy INTEGER
);
"""


def connect_to_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(INIT_SQL)
    conn.commit()
    cur = conn.cursor()
    lock = threading.Lock()
    return {"cur": cur, "conn": conn, "lock": lock}


def run_query(db_connection, query, params=None):
    cur = db_connection["cur"]
    conn = db_connection["conn"]
    lock = db_connection["lock"]

    with lock:
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)
        conn.commit()


def get_query(db_connection, query, params=None):
    cur = db_connection["cur"]
    lock = db_connection["lock"]

    with lock:
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)
        rows = cur.fetchall()

    return rows


def close_db(db_connection):
    db_connection["cur"].close()
    db_connection["conn"].close()


def fetch_unanalyzed_articles(db_connection):
    """Return list of (uid, content_article) for rows where problem_statement IS NULL."""
    return get_query(
        db_connection,
        "SELECT uid, content_article FROM newsolvr WHERE problem_statement IS NULL",
    )


def save_article_analysis(db_connection, uid: int, report: dict) -> None:
    """Saves an LLM-analyzed article to the database."""
    run_query(
        db_connection,
        """UPDATE newsolvr SET
            problem_statement = ?, meaningful_problem = ?, pain_intensity = ?,
            frequency = ?, problem_size = ?, market_growth = ?, willingness_to_pay = ?,
            target_customer_clarity = ?, problem_awareness = ?, competition = ?,
            software_solution = ?, ai_fit = ?, speed_to_mvp = ?,
            business_potential = ?, time_relevancy = ?
        WHERE uid = ?""",
        (
            report["problem_statement"],
            report["meaningful_problem"],
            report["pain_intensity"],
            report["frequency"],
            report["problem_size"],
            report["market_growth"],
            report["willingness_to_pay"],
            report["target_customer_clarity"],
            report["problem_awareness"],
            report["differentiation_potential"],
            report["software_solution"],
            report["ai_fit"],
            report["speed_to_mvp"],
            report["business_potential"],
            report["time_relevancy"],
            uid,
        ),
    )
