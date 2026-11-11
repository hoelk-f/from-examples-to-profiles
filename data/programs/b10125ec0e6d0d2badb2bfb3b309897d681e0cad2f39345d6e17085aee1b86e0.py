def transform(x: str) -> str:
    """
    Extracts the substring after the last semicolon in the input string,
    trimming any leading or trailing whitespace.
    """
    if ';' not in x:
        return x.strip()
    return x.rsplit(';', 1)[-1].strip()