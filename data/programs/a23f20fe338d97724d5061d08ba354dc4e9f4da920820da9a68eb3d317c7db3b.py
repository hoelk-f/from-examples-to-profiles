def transform(x: str) -> str:
    """
    Returns the last whitespace-separated token of the input string.
    """
    tokens = x.strip().split()
    return tokens[-1] if tokens else ""