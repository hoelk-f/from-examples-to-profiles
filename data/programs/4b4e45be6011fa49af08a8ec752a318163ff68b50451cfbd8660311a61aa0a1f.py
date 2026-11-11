def transform(x: str) -> str:
    """
    Extract the three‑letter month abbreviation from a datetime string
    formatted as "DD-MMM-YYYY HH:MM:SS".
    """
    # Split off the time part, then split the date part on hyphens
    parts = x.split()
    if not parts:
        return ""
    date_part = parts[0]
    date_components = date_part.split('-')
    if len(date_components) >= 2:
        return date_components[1]
    return ""