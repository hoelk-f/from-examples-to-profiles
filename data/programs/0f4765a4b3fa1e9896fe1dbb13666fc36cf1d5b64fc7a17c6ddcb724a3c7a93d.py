def transform(x: str) -> str:
    """
    Return the file extension of the given filename.
    If there is no dot in the string, return an empty string.
    """
    parts = x.rsplit('.', 1)
    return parts[1] if len(parts) == 2 else ''