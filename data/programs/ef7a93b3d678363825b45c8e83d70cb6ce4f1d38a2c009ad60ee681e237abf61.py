def transform(x: str) -> str:
    """
    Return the last word of the input string, stripped of surrounding punctuation.
    """
    if not x:
        return ""
    # Split on whitespace and take the last token
    last = x.strip().split()[-1]
    # Strip common punctuation from both ends
    return last.strip('.,!?:;\'"()[]{}')
