def transform(x: str) -> str:
    """
    Extracts the substring after the first '=' character and trims surrounding whitespace.
    If no '=' is present, returns the stripped original string.
    """
    if '=' in x:
        return x.split('=', 1)[1].strip()
    return x.strip()