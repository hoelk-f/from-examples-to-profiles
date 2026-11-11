def transform(x: str) -> str:
    """
    Removes the leading key and '=' sign from the input string,
    returning the trimmed value after the first '='.
    If no '=' is present, returns the stripped input.
    """
    if "=" in x:
        return x.split("=", 1)[1].strip()
    return x.strip()