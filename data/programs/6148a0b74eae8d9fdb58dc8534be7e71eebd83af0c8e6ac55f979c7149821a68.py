def transform(x: str) -> str:
    """
    Returns the file extension of the given filename.
    If there is no dot in the string, returns an empty string.
    """
    if '.' not in x:
        return ''
    return x.rsplit('.', 1)[1]