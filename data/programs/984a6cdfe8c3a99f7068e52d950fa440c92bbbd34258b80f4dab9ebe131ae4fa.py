def transform(x: str) -> str:
    """
    Returns the last word in the input string, assuming words are separated by whitespace.
    """
    # Strip leading/trailing whitespace and split on any whitespace
    parts = x.strip().split()
    # Return the last part if any, otherwise return an empty string
    return parts[-1] if parts else ""