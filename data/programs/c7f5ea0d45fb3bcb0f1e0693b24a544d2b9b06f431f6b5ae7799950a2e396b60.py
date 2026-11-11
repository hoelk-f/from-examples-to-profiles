def transform(x: str) -> str:
    """
    Return the substring after the last '/' character in the input string.
    If '/' is not present, return the original string.
    """
    if '/' in x:
        return x.rsplit('/', 1)[-1]
    return x