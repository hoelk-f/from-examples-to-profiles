def transform(x: str) -> str:
    """Return the first word (substring before the first space) of the input string."""
    return x.split(" ", 1)[0]