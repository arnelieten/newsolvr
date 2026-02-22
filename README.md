# Newsolvr

Pulls tech news from News API, Guardian, and New York Times, extracts article content, and runs it through Gemini to find and score concrete problems. High-scoring problems are displayed in the frontend. Frontend can also filter on niche/global problems and industries.

Available at [newsolvr.lexloop.ink](https://newsolvr.lexloop.ink).

Run the full pipeline with `uv run python -m pipeline`. Needs API keys in `config/.env` (see `.env.example`). See `DEPLOY.md` for deployment.
