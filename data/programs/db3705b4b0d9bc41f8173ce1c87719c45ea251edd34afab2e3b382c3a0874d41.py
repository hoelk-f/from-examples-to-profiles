def transform(x: str) -> str:
    """
    Return the file extension of the given path.
    If there is no extension, return an empty string.
    """
    # Find the last dot in the string
    dot_index = x.rfind('.')
    if dot_index == -1 or dot_index == len(x) - 1:
        return ""
    return x[dot_index + 1:]