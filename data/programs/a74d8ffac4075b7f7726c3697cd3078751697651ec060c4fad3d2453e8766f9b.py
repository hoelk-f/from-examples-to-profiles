def transform(x: str) -> str:
    """
    Returns the substring after the last hyphen in the input string.
    """
    return x.rsplit('-', 1)[-1] if '-' in x else x.strip()