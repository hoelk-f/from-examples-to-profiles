def transform(x: str) -> str:
    """
    Return the portion of the input string that appears before the first comma,
    with surrounding whitespace removed. If there is no comma, return the
    whole string stripped.
    """
    return x.split(",", 1)[0].strip()