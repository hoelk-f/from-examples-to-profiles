def transform(x: str) -> str:
    """Remove the leading abbreviation and space, returning the remainder."""
    parts = x.split(' ', 1)
    return parts[1] if len(parts) > 1 else x