def transform(x: str) -> str:
    """
    Return the file extension of the given filename, preserving the original case.
    If there is no extension, return an empty string.
    """
    parts = x.rsplit('.', 1)
    return parts[1] if len(parts) == 2 else ""