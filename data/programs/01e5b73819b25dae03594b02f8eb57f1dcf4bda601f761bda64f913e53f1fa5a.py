def transform(x: str) -> str:
    """
    Extracts the time range from a flight description string.
    The time range is assumed to be the part after the last semicolon.
    """
    # Split on semicolons and take the last segment
    parts = x.split(';')
    if not parts:
        return ''
    # Strip whitespace from the selected segment
    return parts[-1].strip()