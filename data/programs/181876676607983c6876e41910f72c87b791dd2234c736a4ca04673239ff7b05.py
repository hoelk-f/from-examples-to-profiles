def transform(x: str) -> str:
    """
    Return the first word of the input string, i.e., characters up to the first whitespace.
    """
    return x.split()[0] if x else ""