def transform(x: str) -> str:
    """
    Returns the substring of x before the first colon ':'.
    If no colon is present, returns x unchanged.
    """
    return x.split(":", 1)[0]