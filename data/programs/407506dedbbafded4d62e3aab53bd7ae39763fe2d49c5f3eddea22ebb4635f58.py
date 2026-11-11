def transform(x: str) -> str:
    """Return the part of the string after the first comma, or the original string if no comma."""
    idx = x.find(',')
    return x[idx + 1 :] if idx != -1 else x