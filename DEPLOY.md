# Run pipeline to populate the database

From repo root:

```bash
uv run python -m pipeline
```

# Spin up Flask app (Gunicorn)

From repo root:

```bash
uv run gunicorn -w 2 -b 127.0.0.1:8010 wsgi:application
```
