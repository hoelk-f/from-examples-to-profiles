def transform(x: str) -> str:
    """
    Returns the first word (sequence of characters before the first whitespace) of the input string.
    Leading and trailing whitespace are ignored.
    """
    # Strip leading/trailing whitespace and split on any whitespace
    parts = x.strip().split()
    return parts[0] if parts else ""