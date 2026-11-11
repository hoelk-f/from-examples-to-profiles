def transform(x: str) -> str:
    """Return the last word of the input string."""
    return x.strip().split()[-1] if x.strip() else ""