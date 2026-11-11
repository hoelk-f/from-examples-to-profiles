def transform(x: str) -> str:
    """
    Return the portion of the input string that appears before the first comma,
    with surrounding whitespace removed.
    """
    return x.split(",", 1)[0].strip()