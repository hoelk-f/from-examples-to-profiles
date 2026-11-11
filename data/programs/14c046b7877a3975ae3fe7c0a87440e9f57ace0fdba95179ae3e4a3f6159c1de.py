def transform(x: str) -> str:
    """Return the first word of the input string, or the whole string if it contains no spaces."""
    return x.split()[0] if x.strip() else ""