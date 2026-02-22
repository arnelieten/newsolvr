import logging
from functools import wraps


def handle_pipeline_errors(func):
    """Decorator for pipeline step functions. On exception, logs which function failed and re-raises."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            logging.exception(
                "Pipeline step failed: %s — %s: %s",
                func.__name__,
                type(exc).__name__,
                exc,
            )

    return wrapper
