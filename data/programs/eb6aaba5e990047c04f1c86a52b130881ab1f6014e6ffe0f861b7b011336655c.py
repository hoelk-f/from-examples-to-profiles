def transform(x: str) -> str:
    """
    Return the substring after the last dot in the input string.
    If there is no dot, returns the original string.
    """
    return x.rsplit(".", 1)[-1] if "." in x else x