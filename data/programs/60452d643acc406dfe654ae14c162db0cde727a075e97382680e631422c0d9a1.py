def transform(x: str) -> str:
    """
    Returns the substring after the first comma in the input string,
    with any surrounding whitespace removed.
    """
    parts = x.split(",", 1)
    return parts[1].strip() if len(parts) > 1 else ""