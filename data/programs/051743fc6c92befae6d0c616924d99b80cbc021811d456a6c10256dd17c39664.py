def transform(x: str) -> str:
    """
    Returns the last word of the input string, stripped of surrounding whitespace.
    """
    # Split on any whitespace and return the last non-empty token.
    # If the string is empty or contains no words, return an empty string.
    parts = x.strip().split()
    return parts[-1] if parts else ""