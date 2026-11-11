def transform(x: str) -> str:
    """Return the basename of a path-like string."""
    return x.split('/')[-1] if x else ''