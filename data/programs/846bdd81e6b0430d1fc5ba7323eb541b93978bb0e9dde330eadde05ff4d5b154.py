def transform(x: str) -> str:
    """
    Returns the substring after the last '=' character in the input string,
    with leading and trailing whitespace removed.
    """
    idx = x.rfind("=")
    if idx == -1:
        return ""
    return x[idx + 1 :].strip()