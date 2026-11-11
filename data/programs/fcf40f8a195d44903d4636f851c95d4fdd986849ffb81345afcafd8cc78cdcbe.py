def transform(x: str) -> str:
    """
    Returns the substring of `x` before the first comma, with surrounding whitespace removed.
    If there is no comma, returns the whole string stripped of whitespace.
    """
    return x.split(",", 1)[0].strip()