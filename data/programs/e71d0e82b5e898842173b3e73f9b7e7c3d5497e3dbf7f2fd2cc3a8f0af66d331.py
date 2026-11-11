def transform(x: str) -> str:
    """
    Return the substring after the last '=' character in the input string,
    with surrounding whitespace removed.
    """
    # Split on the last '=', take the part after it.
    # If there is no '=', return the whole string stripped.
    parts = x.rsplit('=', 1)
    return parts[-1].strip()