def transform(x: str) -> str:
    """
    Extract the month name from a date string formatted like:
    "Weekday, 3rd April, 1989"
    """
    # Split on comma followed by optional space
    parts = [part.strip() for part in x.split(',')]
    if len(parts) < 2:
        return ""
    # The part containing day ordinal and month is the second element
    day_month = parts[1]
    # The month is the last word in that part
    month = day_month.split()[-1]
    return month.strip()