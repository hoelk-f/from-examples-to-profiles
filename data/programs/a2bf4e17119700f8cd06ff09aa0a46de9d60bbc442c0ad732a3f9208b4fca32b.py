def transform(x: str) -> str:
    """
    Extract the three-letter month abbreviation from a datetime string
    formatted as "DD-MMM-YYYY HH:MM:SS".
    """
    # Split off the time part and then split the date part by hyphens
    date_part = x.split()[0]
    parts = date_part.split('-')
    if len(parts) >= 2:
        return parts[1]
    # Fallback: return empty string if format is unexpected
    return ""