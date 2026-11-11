def transform(x: str) -> str:
    """
    Extracts the time range from a flight description string.
    The input format contains semicolon-separated parts, and the time range
    is always the last part after the final ';'.
    """
    return x.split(";")[-1].strip()