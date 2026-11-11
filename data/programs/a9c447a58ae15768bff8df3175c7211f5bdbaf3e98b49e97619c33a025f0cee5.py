def transform(x: str) -> str:
    """
    Return the last word of the input string, stripped of surrounding punctuation.
    """
    import string

    # Split by whitespace to get words
    words = x.strip().split()
    if not words:
        return ""
    # Take the last token
    last = words[-1]
    # Strip punctuation from both ends
    return last.strip(string.punctuation)