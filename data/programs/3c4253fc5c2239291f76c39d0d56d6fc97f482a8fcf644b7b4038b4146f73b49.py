def transform(x: str) -> str:
    """
    Extract the four‑digit year from a date‑time string of the form
    'DD-MMM-YYYY HH:MM:SS'.
    """
    # Split off the time part, then split the date part by hyphens.
    date_part = x.split()[0]
    parts = date_part.split('-')
    if len(parts) >= 3:
        return parts[2]
    # Fallback: find a 4‑digit number in the string.
    import re
    match = re.search(r'\b\d{4}\b', x)
    return match.group(0) if match else ''