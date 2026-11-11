def transform(x: str) -> str:
    # Split the date-time string, isolate the date part, then extract the month abbreviation.
    date_part = x.split()[0]  # e.g., "13-Jan-2038"
    parts = date_part.split('-')
    return parts[1] if len(parts) > 1 else ""