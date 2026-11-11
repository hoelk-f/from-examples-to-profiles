def transform(x: str) -> str:
    """
    Returns the substring of `x` that appears before the first hyphen.
    If there is no hyphen in the string, the whole string is returned.
    """
    return x.split('-', 1)[0]