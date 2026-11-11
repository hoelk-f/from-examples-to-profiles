def transform(x: str) -> str:
    """
    Returns the middle segment of a hyphen-separated string.
    Example: "332-395-493" -> "395"
    """
    parts = x.split('-')
    return parts[1] if len(parts) > 1 else ''