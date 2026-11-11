def transform(x: str) -> str:
    """
    Returns the portion of the input string before the first comma,
    with surrounding whitespace removed.
    """
    return x.split(",", 1)[0].strip()