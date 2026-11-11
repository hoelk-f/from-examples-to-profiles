def transform(x: str) -> str:
    """
    Return the last whitespace-separated token of the input string.
    """
    # Split on whitespace and return the last part
    parts = x.split()
    return parts[-1] if parts else ""