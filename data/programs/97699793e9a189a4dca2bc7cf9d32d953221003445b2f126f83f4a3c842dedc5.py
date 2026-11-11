def transform(x: str) -> str:
    """
    Returns the substring after the last space in the input string.
    If there is no space, returns the whole string.
    """
    return x.rsplit(' ', 1)[-1]