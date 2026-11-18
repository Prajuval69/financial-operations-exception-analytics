from datetime import datetime, timezone
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")


def parse_date(value: Any) -> datetime | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc).replace(tzinfo=None) if parsed.tzinfo else parsed
    except (ValueError, TypeError):
        return None


def age_days(detected_at: str, as_of: str) -> float:
    detected, end = parse_date(detected_at), parse_date(as_of)
    if detected is None or end is None:
        raise ValueError("Aging requires valid ISO timestamps")
    return max(0.0, (end - detected).total_seconds() / 86400)


def aging_bucket(days: float, boundaries: list[int]) -> str:
    lower = 0
    for upper in boundaries:
        if days <= upper:
            return f"{lower}–{upper} days"
        lower = upper
    return f">{boundaries[-1]} days"
