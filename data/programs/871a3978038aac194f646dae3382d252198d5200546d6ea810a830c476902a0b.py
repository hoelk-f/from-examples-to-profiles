def transform(x: str) -> str:
    """
    Remove the leading label up to the first colon and any following whitespace.
    """
    parts = x.split(":", 1)
    if len(parts) == 2:
        return parts[1].lstrip()
    return x.lstrip()