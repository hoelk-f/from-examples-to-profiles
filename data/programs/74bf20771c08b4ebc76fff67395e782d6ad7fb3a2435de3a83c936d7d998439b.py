def transform(x: str) -> str:
    """Return the substring after the last period in the input string."""
    idx = x.rfind('.')
    return x[idx + 1:] if idx != -1 else ''