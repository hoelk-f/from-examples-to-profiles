def transform(x: str) -> str:
    # Try to extract the year from a typical "dd-MMM-yyyy HH:MM:SS" format
    parts = x.split()
    if parts:
        date_part = parts[0]
        subparts = date_part.split('-')
        if len(subparts) >= 3:
            return subparts[2]
    # Fallback: first 4‑digit number in the string
    import re
    m = re.search(r'\b\d{4}\b', x)
    return m.group(0) if m else ""