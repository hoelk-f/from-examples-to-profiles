def transform(x: str) -> str:
    """
    Extracts the time range (including any day offset) from a flight description string.
    The input format is assumed to contain semicolon-separated sections, with the
    last section representing the time range.
    """
    return x.split(";")[-1].strip()