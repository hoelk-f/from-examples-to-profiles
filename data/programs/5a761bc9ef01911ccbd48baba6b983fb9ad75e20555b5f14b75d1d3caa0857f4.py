def transform(x: str) -> str:
    """
    Return the last word of the input string, stripped of common trailing punctuation.
    """
    # Split the string into words based on whitespace
    words = x.strip().split()
    if not words:
        return ""
    # Take the last word
    last = words[-1]
    # Remove trailing punctuation characters
    return last.rstrip('.,!?:;\'"')