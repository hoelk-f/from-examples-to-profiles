def transform(x: str) -> str:
    """
    Returns the first word of the input string, defined as the sequence of characters
    before the first whitespace. If the string contains no whitespace, returns the
    entire string.
    """
    # Use split with default whitespace handling to get the first token.
    return x.split()[0] if x.strip() else ""