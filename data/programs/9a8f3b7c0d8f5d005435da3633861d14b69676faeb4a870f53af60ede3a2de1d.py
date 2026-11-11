def transform(x: str) -> str:
    """
    Extracts the month name from a date string formatted like:
    "Weekday, Dth Month, Year"
    """
    # Split on commas; the month is in the second segment.
    parts = x.split(',')
    if len(parts) < 2:
        return ""
    # Trim whitespace and split the segment containing day and month.
    day_month = parts[1].strip()
    tokens = day_month.split()
    if not tokens:
        return ""
    # The month is the last token.
    return tokens[-1]