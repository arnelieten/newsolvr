-- SQLite schema (table is created automatically on first connect via db_utils).
-- For reference only:
CREATE TABLE IF NOT EXISTS newsolvr (
    uid INTEGER PRIMARY KEY AUTOINCREMENT,
    title_article TEXT,
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
