def transform(x: str) -> str:
    """
    Extracts the time range segment from a flight description string.
    The time range is assumed to be the part after the last semicolon.
    Leading and trailing whitespace are removed.
    """
    return x.split(';')[-1].strip()