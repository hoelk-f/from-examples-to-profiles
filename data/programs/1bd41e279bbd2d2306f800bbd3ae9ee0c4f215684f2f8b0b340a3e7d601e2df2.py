def transform(x: str) -> str:
    """Return the file extension of the given filename (text after the last dot)."""
    idx = x.rfind('.')
    return x[idx + 1 :] if idx != -1 else ""