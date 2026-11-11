def transform(x: str) -> str:
    """
    Extracts the last whitespace-separated token from the input string.
    """
    return x.strip().split()[-1]