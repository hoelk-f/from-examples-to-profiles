def transform(x: str) -> str:
    """
    Returns the substring of `x` that appears before the first hyphen ('-').
    If there is no hyphen in the input, the original string is returned.
    """
    idx = x.find('-')
    return x[:idx] if idx != -1 else x