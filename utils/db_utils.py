import csv
import os
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
    problem_verified TEXT,
    problem_summary TEXT,
    evidence_from_article TEXT,
    startup_idea TEXT,
    why_now TEXT,
    early_adopters TEXT
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


NEWSOLVR_COLUMNS = (
    "uid",
    "title_article",
    "description_article",
    "content_article",
    "link_article",
    "published_date",
    "problem_verified",
    "problem_summary",
    "evidence_from_article",
    "startup_idea",
    "why_now",
    "early_adopters",
)


def export_db_to_csv():
    out = os.path.join(os.path.dirname(__file__), "..", "database", "db_export.csv")
    db = connect_to_db()
    try:
        rows = get_query(db, f"SELECT {', '.join(NEWSOLVR_COLUMNS)} FROM newsolvr ORDER BY uid")
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(NEWSOLVR_COLUMNS)
            w.writerows(["" if v is None else v for v in row] for row in rows)
        return len(rows)
    finally:
        close_db(db)
