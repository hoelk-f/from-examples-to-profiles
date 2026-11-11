def transform(x: str) -> str:
    """
    Returns the substring after the last hyphen in the input string.
    """
    return x.strip().split("-")[-1]