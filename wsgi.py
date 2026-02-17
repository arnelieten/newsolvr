"""Gunicorn production server implementation."""

from app import create_app

application = create_app()
