def transform(x: str) -> str:
    """
    Extracts the domain part of an email address, i.e., the substring after the first '@'.
    """
    parts = x.split('@', 1)
    return parts[1] if len(parts) > 1 else ''