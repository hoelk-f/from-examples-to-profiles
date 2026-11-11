def transform(x: str) -> str:
    """
    Extracts the domain part of an email address.
    Returns the substring after the first '@' character,
    or an empty string if '@' is not present.
    """
    parts = x.split('@', 1)
    return parts[1] if len(parts) == 2 else ''