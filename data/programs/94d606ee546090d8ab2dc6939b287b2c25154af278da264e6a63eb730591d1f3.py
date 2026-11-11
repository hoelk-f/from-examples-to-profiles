def transform(x: str) -> str:
    """Return the substring after the last '/' in the input string."""
    return x.rsplit('/', 1)[-1] if '/' in x else x