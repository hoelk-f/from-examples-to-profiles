def transform(x: str) -> str:
    """
    Return the file extension of the given path string.
    The extension is defined as the substring after the last '.' character.
    If there is no '.' in the string, an empty string is returned.
    """
    _, _, ext = x.rpartition('.')
    return ext