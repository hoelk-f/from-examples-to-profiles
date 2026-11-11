def transform(x: str) -> str:
    """Return the part of the string after the first '@' character."""
    try:
        return x.split("@", 1)[1]
    except IndexError:
        return ""