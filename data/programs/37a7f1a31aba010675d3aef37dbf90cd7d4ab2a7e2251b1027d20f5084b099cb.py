def transform(x: str) -> str:
    """
    Extracts and returns the domain part of an email address.
    If no '@' is present, returns the original string.
    """
    parts = x.split("@", 1)
    return parts[1] if len(parts) == 2 else x