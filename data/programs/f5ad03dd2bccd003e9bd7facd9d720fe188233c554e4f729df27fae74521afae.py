def transform(x: str) -> str:
    """
    Removes the prefix up to the first '=' character and strips surrounding whitespace.
    If no '=' is present, returns the original string stripped of whitespace.
    """
    if '=' in x:
        return x.split('=', 1)[1].strip()
    return x.strip()