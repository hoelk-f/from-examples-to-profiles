def transform(x: str) -> str:
    """
    Returns the substring after the last whitespace in the input string.
    If there is no whitespace, returns the original string.
    """
    parts = x.rsplit(None, 1)
    return parts[-1] if parts else ""