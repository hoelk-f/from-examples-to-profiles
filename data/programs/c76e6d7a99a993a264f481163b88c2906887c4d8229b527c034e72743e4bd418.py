def transform(x: str) -> str:
    """
    Return the last word of the input string, stripped of common trailing punctuation.
    """
    if not x:
        return ""
    # Split on whitespace and take the last token
    last_token = x.strip().split()[-1]
    # Remove trailing punctuation characters
    return last_token.rstrip('.,!?:;')