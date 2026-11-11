def transform(x: str) -> str:
    """
    Returns the substring after the last hyphen in the input string.
    If there is no hyphen, returns the original string.
    """
    parts = x.rsplit('-', 1)
    return parts[-1] if len(parts) > 1 else x