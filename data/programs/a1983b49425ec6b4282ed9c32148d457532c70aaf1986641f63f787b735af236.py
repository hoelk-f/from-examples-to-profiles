def transform(x: str) -> str:
    """
    Extracts the portion of the string after the first comma,
    trimming any surrounding whitespace.
    """
    # Split on the first comma
    parts = x.split(",", 1)
    # If there is no comma, return the original string stripped
    if len(parts) == 1:
        return parts[0].strip()
    # Return the part after the comma, stripped of whitespace
    return parts[1].strip()