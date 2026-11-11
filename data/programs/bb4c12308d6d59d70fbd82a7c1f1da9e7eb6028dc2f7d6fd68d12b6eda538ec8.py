def transform(x: str) -> str:
    """
    Return the last word of the input string, stripped of surrounding punctuation.
    """
    if not x:
        return ""
    # Split on whitespace
    words = x.strip().split()
    if not words:
        return ""
    last = words[-1]
    # Strip common punctuation from both ends
    return last.strip(".,!?:;\"'`()[]{}")