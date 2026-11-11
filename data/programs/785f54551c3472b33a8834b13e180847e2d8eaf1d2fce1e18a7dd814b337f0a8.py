def transform(x: str) -> str:
    """
    Extracts the year from a datetime string formatted as
    'DD-Mmm-YYYY hh:mm:ss'.
    """
    # Split off the time part, then split the date part by hyphens.
    parts = x.split()
    if not parts:
        return ""
    date_part = parts[0]
    date_fields = date_part.split('-')
    if len(date_fields) < 3:
        return ""
    return date_fields[2]