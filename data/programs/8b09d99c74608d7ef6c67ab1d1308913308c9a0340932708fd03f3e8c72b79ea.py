def transform(x: str) -> str:
    """
    Extracts the substring before the first '.' in the given string.
    If no '.' is present, returns the whole string.
    """
    return x.split(".", 1)[0]