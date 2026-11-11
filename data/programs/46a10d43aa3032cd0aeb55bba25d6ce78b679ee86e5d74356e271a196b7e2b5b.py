def transform(x: str) -> str:
    """
    Returns the first word of the input string, where words are separated by whitespace.
    If the input is empty or contains no words, returns an empty string.
    """
    parts = x.strip().split()
    return parts[0] if parts else ""