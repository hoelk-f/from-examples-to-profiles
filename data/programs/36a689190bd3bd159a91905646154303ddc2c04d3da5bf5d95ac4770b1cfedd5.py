def transform(x: str) -> str:
    """
    Extracts the substring after the last semicolon in the input string,
    stripping any leading/trailing whitespace.
    """
    idx = x.rfind(';')
    if idx == -1:
        return x.strip()
    return x[idx + 1 :].strip()