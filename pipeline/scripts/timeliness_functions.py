"""Timeliness scoring: older articles get fewer points. Uses standard library only."""

from datetime import datetime, timezone


def parse_published_date(published_date: str | None) -> datetime | None:
    """Parse DB string (ISO with time, date-only, or empty). Returns None on missing/invalid."""
    if not published_date or not str(published_date).strip():
        return None
    s = str(published_date).strip()
    # ISO with time (e.g. 2025-02-21T12:00:00Z or 2025-02-21T12:00:00+00:00)
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        pass
    # Date-only (e.g. 2025-02-21)
    try:
        dt = datetime.strptime(s[:10], "%Y-%m-%d")
        return dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        pass
    return None


def days_ago(
    published_date: str | None,
    reference: datetime | None = None,
) -> float:
    """Days from published_date to reference (default now UTC). Positive = in the past. Large value on parse failure."""
    ref = reference or datetime.now(timezone.utc)
    if ref.tzinfo is None:
        ref = ref.replace(tzinfo=timezone.utc)
    parsed = parse_published_date(published_date)
    if parsed is None:
        return 365.0  # cap so timeliness_score becomes ~0
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    delta = ref - parsed
    return max(0.0, delta.total_seconds() / 86400.0)


def timeliness_score(
    published_date: str | None,
    *,
    reference: datetime | None = None,
) -> float:
    """Return multiplier in [0, 1]: 1 (day 1), 0.99 (day 2), 0.95 (day 3), 0.9 (day 4), 0.8 (day 5+)."""
    days = days_ago(published_date, reference=reference)
    table = {0: 1.0, 1: 0.99, 2: 0.95, 3: 0.9, 4: 0.8}
    if days <= 4:
        return table[int(days)]
    return 0.8
