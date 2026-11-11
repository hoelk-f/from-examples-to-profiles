def transform(x: str) -> str:
    """
    Return the file extension of a path string (the substring after the last dot).
    If there is no dot in the string, return an empty string.
    """
    # Find the last dot in the string
    idx = x.rfind('.')
    if idx == -1:
        return ''
    return x[idx + 1:]