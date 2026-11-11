def transform(x: str) -> str:
    """
    Extracts the substring after the first '=' character and strips surrounding whitespace.
    """
    if "=" not in x:
        return x.strip()
    _, after = x.split("=", 1)
    return after.strip()