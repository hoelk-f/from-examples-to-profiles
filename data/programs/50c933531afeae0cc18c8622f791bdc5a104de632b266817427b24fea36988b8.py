def transform(x: str) -> str:
    """Remove a trailing period from the string, if present."""
    return x[:-1] if x.endswith('.') else x