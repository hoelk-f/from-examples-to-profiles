def transform(x: str) -> str:
    """
    Extract the day component (two digits) from an ISO 8601 datetime string.
    Expected format: YYYY-MM-DDThh:mm:ssZ
    """
    # Primary fast path using fixed positions
    if len(x) >= 10:
        day = x[8:10]
        if day.isdigit():
            return day
    # Fallback parsing
    date_part = x.split('T', 1)[0]
    parts = date_part.split('-')
    return parts[2] if len(parts) >= 3 else ''