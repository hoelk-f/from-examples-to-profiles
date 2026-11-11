def transform(x: str) -> str:
    """
    Remove the first word (up to the first space) from the input string.
    If there is no space, returns the original string.
    """
    # Find the first space
    _, sep, rest = x.partition(' ')
    # If a space was found, return the rest; otherwise return the original string
    return rest if sep else x