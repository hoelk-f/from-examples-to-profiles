def transform(x: str) -> str:
    """
    Returns the first word of the input string, defined as the characters
    before the first space. Leading and trailing whitespace are ignored.
    """
    return x.strip().split(' ', 1)[0]