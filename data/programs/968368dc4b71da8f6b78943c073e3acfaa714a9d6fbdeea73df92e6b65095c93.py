def transform(x: str) -> str:
    """
    Extracts the seconds component from a timestamp string formatted as
    'dd-MMM-yyyy HH:MM:SS'.
    """
    # Split off the time part after the space
    parts = x.split()
    if not parts:
        return ""
    time_part = parts[-1]
    # Split the time by colon and return the last segment (seconds)
    time_components = time_part.split(":")
    return time_components[-1] if time_components else ""