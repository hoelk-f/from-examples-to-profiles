def transform(x: str) -> str:
    """
    Returns the text after the last '=' character in the input string,
    with leading and trailing whitespace removed.
    """
    if '=' not in x:
        return ''
    return x.rsplit('=', 1)[-1].strip()