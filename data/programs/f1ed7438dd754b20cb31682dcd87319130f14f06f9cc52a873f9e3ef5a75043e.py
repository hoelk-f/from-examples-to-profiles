def transform(x: str) -> str:
    """
    Extracts the filename from a typical file listing line.
    Returns the last whitespace-separated token.
    """
    parts = x.split()
    return parts[-1] if parts else ""