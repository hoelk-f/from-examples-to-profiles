def transform(x: str) -> str:
    """
    Extracts the minutes component from a datetime string formatted like:
    'DD-Mon-YYYY HH:MM:SS' and returns it as a string.
    """
    # Split off the time part after the last space
    try:
        time_part = x.rsplit(' ', 1)[1]
    except IndexError:
        return ""
    # Split the time into hour, minute, second
    parts = time_part.split(':')
    if len(parts) >= 2:
        return parts[1]
    return ""