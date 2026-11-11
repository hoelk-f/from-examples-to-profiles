def transform(x: str) -> str:
    """
    Extracts the substring before the first dot in the input string.
    If there is no dot, returns the part before the '@' symbol,
    or the whole string if neither are present.
    """
    if '.' in x:
        return x.split('.', 1)[0]
    if '@' in x:
        return x.split('@', 1)[0]
    return x