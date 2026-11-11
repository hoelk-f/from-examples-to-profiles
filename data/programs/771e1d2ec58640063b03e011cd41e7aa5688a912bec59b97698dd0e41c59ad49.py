def transform(x: str) -> str:
    """
    Extracts the time range from a flight description string.
    The input format contains semicolon-separated sections, and the
    last section holds the departure and arrival times.
    """
    return x.split(';')[-1].strip()