def transform(x: str) -> str:
    """Return the first word (token) of the input string."""
    return x.split()[0] if x else ""