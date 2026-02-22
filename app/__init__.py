from flask import Flask, render_template, request

from database import ALLOWED_INDUSTRIES, close_db, connect_to_db, fetch_top_ranked_problems

# Human-readable labels for industry filter and badges (key = stored value, value = display).
INDUSTRY_DISPLAY_LABELS = {
    "healthcare": "Healthcare",
    "technology": "Technology",
    "manufacturing": "Manufacturing",
    "financial_services": "Financial services",
    "education": "Education",
    "energy": "Energy",
    "government": "Government",
    "other": "Other",
}


def create_app():
    app = Flask(__name__)

    @app.route("/")
    def index():
        problem_size_filter = request.args.get("problem_size")
        if problem_size_filter not in ("niche", "global"):
            problem_size_filter = None
        industry_filter = request.args.get("industry")
        if industry_filter not in ALLOWED_INDUSTRIES:
            industry_filter = None
        db = connect_to_db()
        try:
            problems = fetch_top_ranked_problems(
                db,
                limit=20,
                problem_size=problem_size_filter,
                industry=industry_filter,
            )
            return render_template(
                "index.html",
                problems=problems,
                problem_size_filter=problem_size_filter,
                industry_filter=industry_filter,
                allowed_industries=ALLOWED_INDUSTRIES,
                industry_display_labels=INDUSTRY_DISPLAY_LABELS,
            )
        finally:
            close_db(db)

    return app


app = create_app()
