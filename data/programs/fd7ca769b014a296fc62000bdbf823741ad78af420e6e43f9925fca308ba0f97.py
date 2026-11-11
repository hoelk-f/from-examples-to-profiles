def transform(x: str) -> str:
    """
    Extracts the leading numeric token (typically a year) from the input string.
    """
    # Split the string on whitespace and return the first segment.
    return x.split()[0] if x else ""