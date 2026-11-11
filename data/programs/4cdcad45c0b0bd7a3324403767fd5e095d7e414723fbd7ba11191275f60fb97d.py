def transform(x: str) -> str:
    """
    Returns the substring of the input up to (but not including) the first colon.
    If no colon is present, returns the original string.
    """
    return x.split(":", 1)[0] if ":" in x else x