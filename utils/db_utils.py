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

RANKING_COLUMNS = (
    "meaningful_problem",
    "pain_intensity",
    "frequency",
    "problem_size",
    "market_growth",
    "willingness_to_pay",
    "target_customer_clarity",
    "problem_awareness",
    "differentiation_potential",
    "software_solution",
    "ai_fit",
    "speed_to_mvp",
    "business_potential",
    "time_relevancy",
)


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
