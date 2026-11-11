def transform(x: str) -> str:
    """
    Returns the part of the input string that appears before the first '=' character.
    If the character is not present, the whole string is returned.
    """
    return x.split('=', 1)[0]