def transform(x: str) -> str:
    """
    Returns the first word of the input string, i.e., the substring before the first whitespace.
    """
    return x.split()[0] if x else ""