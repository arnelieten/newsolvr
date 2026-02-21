from flask import Flask, render_template

from database import close_db, connect_to_db, fetch_top_ranked_problems


def create_app():
    app = Flask(__name__)

    @app.route("/")
    def index():
        db = connect_to_db()
        try:
            problems = fetch_top_ranked_problems(db, limit=20)
            return render_template("index.html", problems=problems)
        finally:
            close_db(db)

    return app


app = create_app()
