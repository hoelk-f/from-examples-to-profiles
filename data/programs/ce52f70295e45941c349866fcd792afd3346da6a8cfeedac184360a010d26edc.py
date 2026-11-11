def transform(x: str) -> str:
    """
    Return the substring after the first '=' character, stripped of surrounding whitespace.
    If no '=' is present, return the original string stripped of whitespace.
    """
    parts = x.split("=", 1)
    if len(parts) == 2:
        return parts[1].strip()
    return x.strip()