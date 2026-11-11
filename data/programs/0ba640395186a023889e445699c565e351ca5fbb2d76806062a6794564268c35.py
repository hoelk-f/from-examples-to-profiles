def transform(x: str) -> str:
    """
    Extracts and returns the last whitespace-separated token from the input string.
    """
    return x.strip().split()[-1]