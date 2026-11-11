def transform(x: str) -> str:
    """
    Return the substring after the last '/' character.
    If no '/' is present, return the original string.
    """
    return x.rsplit('/', 1)[-1] if '/' in x else x