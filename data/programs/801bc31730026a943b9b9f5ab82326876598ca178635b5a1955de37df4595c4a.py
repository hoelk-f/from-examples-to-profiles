def transform(x: str) -> str:
    """
    Extracts the month abbreviation from a datetime string formatted as
    'DD-MMM-YYYY HH:MM:SS' and returns it.
    """
    # Split off the time part and focus on the date portion
    date_part = x.split()[0] if x else ""
    # Split the date by hyphens and return the month component if present
    parts = date_part.split('-')
    return parts[1] if len(parts) >= 3 else ""