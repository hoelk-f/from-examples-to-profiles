def transform(x: str) -> str:
    """
    Removes a leading key and equals sign from the string, returning the value part.
    If an '=' character is present, returns the substring after the first '=', stripped
    of surrounding whitespace. Otherwise, returns the original string stripped.
    """
    if '=' in x:
        return x.split('=', 1)[1].strip()
    return x.strip()