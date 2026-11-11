def transform(x: str) -> str:
    """
    Returns the last word of the input string, assuming words are separated by whitespace.
    """
    # Strip leading/trailing whitespace and split on any whitespace
    parts = x.strip().split()
    return parts[-1] if parts else ""