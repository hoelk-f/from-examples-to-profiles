def transform(x: str) -> str:
    """
    Extracts the last whitespace-separated token from the input string.
    """
    return x.split()[-1] if x else ""