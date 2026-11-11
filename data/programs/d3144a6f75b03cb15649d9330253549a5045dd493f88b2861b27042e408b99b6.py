def transform(x: str) -> str:
    """
    Return the substring after the last '/' in the input string.
    If '/' is not present, returns the original string.
    """
    return x.rsplit('/', 1)[-1]