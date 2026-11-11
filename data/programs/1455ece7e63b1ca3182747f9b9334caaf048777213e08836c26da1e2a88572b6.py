def transform(x: str) -> str:
    """
    Extract the time range segment from a flight description string.
    The input format typically contains semicolon-separated sections,
    with the last section representing the departure and arrival times.
    """
    parts = x.split(';')
    if len(parts) < 2:
        return ''
    return parts[-1].strip()