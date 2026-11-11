def transform(x: str) -> str:
    """
    Extracts the leading word (presumably a month name) from a date string.
    """
    # Strip leading/trailing whitespace and split on any whitespace.
    parts = x.strip().split()
    return parts[0] if parts else ""