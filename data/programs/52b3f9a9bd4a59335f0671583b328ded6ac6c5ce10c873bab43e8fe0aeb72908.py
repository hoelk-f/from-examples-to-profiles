def transform(x: str) -> str:
    """
    Remove the trailing Twitter handle (or any text starting with ' @')
    from the input string, returning only the preceding name part.
    """
    parts = x.split(" @", 1)
    return parts[0] if parts else x