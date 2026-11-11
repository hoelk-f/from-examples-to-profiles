def transform(x: str) -> str:
    """
    Remove a leading dollar sign from the input string, if present.
    Leaves the rest of the string unchanged.
    """
    return x[1:] if x.startswith('$') else x