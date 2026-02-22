import sqlite3
import threading

from config.config import DB_PATH

ALLOWED_INDUSTRIES = (
    "healthcare",
    "technology",
    "manufacturing",
    "financial_services",
    "education",
    "energy",
    "government",
    "other",
)

INIT_SQL = """
CREATE TABLE IF NOT EXISTS newsolvr (
    uid INTEGER PRIMARY KEY AUTOINCREMENT,
    title_article TEXT,
    content_article TEXT,
    link_article TEXT UNIQUE,
    published_date TEXT,
    problem_summary TEXT,
    problem_statement TEXT,
    meaningful_problem INTEGER,
    pain_intensity INTEGER,
    frequency INTEGER,
    problem_size TEXT,
    industry TEXT,
    market_growth INTEGER,
    willingness_to_pay INTEGER,
    target_customer_clarity INTEGER,
    problem_awareness INTEGER,
    competition INTEGER,
    software_solution INTEGER,
    ai_fit INTEGER,
    speed_to_mvp INTEGER,
    business_potential INTEGER,
    time_relevancy INTEGER,
    total_score INTEGER
);
"""


def connect_to_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(INIT_SQL)
    conn.commit()
    try:
        conn.execute("ALTER TABLE newsolvr ADD COLUMN problem_summary TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # column already exists
    try:
        conn.execute("ALTER TABLE newsolvr ADD COLUMN industry TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # column already exists
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
    """Return list of (uid, link_article, content_article) for rows where problem_statement IS NULL."""
    return get_query(
        db_connection,
        "SELECT uid, link_article, content_article FROM newsolvr WHERE problem_statement IS NULL",
    )


def fetch_top_ranked_problems(
    db_connection,
    limit: int = 20,
    problem_size: str | None = None,
    industry: str | None = None,
) -> list[dict[str, str | int | None]]:
    """Return top rows by total_score (desc). Each item includes problem_summary, problem_statement, link_article, score, problem_size, industry. Optionally filter by problem_size and/or industry."""
    conditions = ["problem_statement IS NOT NULL"]
    params: list[str | int] = []
    if problem_size in ("niche", "global"):
        conditions.append("problem_size = ?")
        params.append(problem_size)
    if industry in ALLOWED_INDUSTRIES:
        conditions.append("industry = ?")
        params.append(industry)
    params.append(limit)
    where = " AND ".join(conditions)
    query = f"""SELECT problem_summary, problem_statement, link_article, total_score, problem_size, industry FROM newsolvr
                   WHERE {where}
                   ORDER BY total_score DESC NULLS LAST LIMIT ?"""
    rows = get_query(db_connection, query, tuple(params))
    return [
        {
            "problem_summary": row[0] or "",
            "problem_statement": row[1] or "",
            "link_article": row[2] or "",
            "score": row[3] if row[3] is not None else 0,
            "problem_size": row[4] if len(row) > 4 else None,
            "industry": row[5] if len(row) > 5 else None,
        }
        for row in rows
    ]


def update_article_content(db_connection, uid: int, content: str) -> None:
    """Update content_article for the given uid."""
    run_query(
        db_connection,
        "UPDATE newsolvr SET content_article = ? WHERE uid = ?",
        (content, uid),
    )


def save_article_analysis(db_connection, uid: int, report: dict) -> None:
    """Saves an LLM-analyzed article to the database."""
    problem_size = report["problem_size"]
    if isinstance(problem_size, str):
        problem_size = problem_size.strip().lower()
    industry = report["industry"]
    if isinstance(industry, str):
        industry = industry.strip().lower().replace(" ", "_")
    run_query(
        db_connection,
        """UPDATE newsolvr SET
            problem_summary = ?, problem_statement = ?, meaningful_problem = ?, pain_intensity = ?,
            frequency = ?, problem_size = ?, industry = ?, market_growth = ?, willingness_to_pay = ?,
            target_customer_clarity = ?, problem_awareness = ?, competition = ?,
            software_solution = ?, ai_fit = ?, speed_to_mvp = ?,
            business_potential = ?, time_relevancy = ?
        WHERE uid = ?""",
        (
            report["problem_summary"],
            report["problem_statement"],
            report["meaningful_problem"],
            report["pain_intensity"],
            report["frequency"],
            problem_size,
            industry,
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
