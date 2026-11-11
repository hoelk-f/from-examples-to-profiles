def transform(x: str) -> str:
    """
    Return the part of the input string before the first '=' character.
    If there is no '=', the whole string is returned.
    """
    return x.split('=', 1)[0]