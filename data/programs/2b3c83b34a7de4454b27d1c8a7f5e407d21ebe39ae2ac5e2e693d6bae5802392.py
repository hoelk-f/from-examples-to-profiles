def transform(x: str) -> str:
    """
    Return the last word of the input string, stripped of surrounding punctuation.
    """
    # Split on whitespace to get tokens
    tokens = x.strip().split()
    if not tokens:
        return ""
    # Take the last token and strip common punctuation characters
    last = tokens[-1].strip(".,!?;:\"'()[]{}")
    return last