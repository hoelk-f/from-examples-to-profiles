def transform(x: str) -> str:
    """Remove a leading dollar sign from the string, if present."""
    return x[1:] if x.startswith('$') else x