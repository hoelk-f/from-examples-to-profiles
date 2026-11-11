def transform(x: str) -> str:
    """
    Returns the first whitespace-separated token of the input string.
    Leading/trailing whitespace is ignored. If the string is empty or
    contains no whitespace, the original (stripped) string is returned.
    """
    # Strip leading/trailing whitespace and split on any whitespace
    parts = x.strip().split()
    return parts[0] if parts else ""