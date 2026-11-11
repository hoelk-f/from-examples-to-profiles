def transform(x: str) -> str:
    """
    Returns the substring after the last hyphen in the input string.
    If no hyphen is present, returns the original string.
    """
    idx = x.rfind('-')
    return x[idx + 1 :] if idx != -1 else x