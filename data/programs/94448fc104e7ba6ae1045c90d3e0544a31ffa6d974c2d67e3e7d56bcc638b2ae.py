def transform(x: str) -> str:
    """
    Returns the last whitespace-separated token of the input string.
    If the string is empty or contains only whitespace, returns an empty string.
    """
    tokens = x.strip().split()
    return tokens[-1] if tokens else ""