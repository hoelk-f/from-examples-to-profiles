def transform(x: str) -> str:
    """
    Return the first word of the input string, defined as the substring before the first space.
    If there is no space, returns the original string.
    """
    return x.split(' ', 1)[0]