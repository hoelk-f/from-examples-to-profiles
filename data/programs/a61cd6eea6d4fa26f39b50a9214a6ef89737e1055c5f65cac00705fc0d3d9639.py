def transform(x: str) -> str:
    """
    Extracts the time range from a flight information string.
    The time range is assumed to be the substring after the last semicolon.
    """
    return x.split(";")[-1].strip()