# Deploying Newsolvr web app on Ubuntu

Run the Flask frontend on your own Ubuntu server with the same SQLite DB as the pipeline.

## Prerequisites

- Python 3.12+
- `uv` (recommended) or `pip`

## Steps

1. **Clone and install**

   ```bash
   cd /path/to/newsolvr
   uv sync   # or: pip install -e .
   ```

2. **Configure environment**

   Copy the example env and set at least `DB_PATH` to your SQLite file (same path the pipeline uses if both run on the same machine):

   ```bash
   cp config/.env.example config/.env
   # Edit config/.env and set DB_PATH=/path/to/newsolvr.db
   ```

3. **Run the app**

   - **Development**: from the project root  
     `flask --app app run`  
     or  
     `python -m flask --app app run`

   - **Production (Gunicorn)**  
     From the project root (so `config/.env` and the app are found):

     ```bash
     gunicorn -w 4 -b 0.0.0.0:8000 "app:app"
     ```

     Then open `http://<server-ip>:8000`. Use a reverse proxy (e.g. Nginx) and/or systemd for a long-running service.

## Optional: systemd

Create `/etc/systemd/system/newsolvr.service`:

```ini
[Unit]
Description=Newsolvr web app
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/path/to/newsolvr
Environment=PATH=/path/to/newsolvr/.venv/bin
ExecStart=/path/to/newsolvr/.venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 "app:app"
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Then: `sudo systemctl daemon-reload`, `sudo systemctl enable newsolvr`, `sudo systemctl start newsolvr`.

## Notes

- The app only reads from the DB; the pipeline can write to the same SQLite file from the same host.
- To run the pipeline from the project root: `python -m pipeline` (or `uv run python -m pipeline`).
- No Redis or extra services required.
