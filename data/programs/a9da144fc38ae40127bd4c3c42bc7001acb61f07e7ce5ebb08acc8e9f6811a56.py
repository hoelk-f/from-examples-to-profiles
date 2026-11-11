def transform(x: str) -> str:
    """
    Return the first whitespace-separated token of the input string.
    """
    tokens = x.strip().split()
    return tokens[0] if tokens else ""