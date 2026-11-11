def transform(x: str) -> str:
    """
    Return the last word of the input string, assuming words are separated by spaces.
    If there is no space in the string, return it unchanged.
    """
    return x.rsplit(' ', 1)[-1] if x else ''