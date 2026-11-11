def transform(x: str) -> str:
    """
    Extracts the time range segment from a flight description string.
    The time range is the part after the last semicolon.
    """
    # Find the last semicolon and take everything after it
    idx = x.rfind(';')
    if idx == -1:
        # No semicolon found; return the whole string stripped
        return x.strip()
    # Slice after the semicolon and strip surrounding whitespace
    return x[idx + 1 :].strip()