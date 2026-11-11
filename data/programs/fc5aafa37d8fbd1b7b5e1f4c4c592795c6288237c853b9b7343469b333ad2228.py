def transform(x: str) -> str:
    """
    Return the last whitespace-separated token of the input string.
    """
    return x.strip().split()[-1]