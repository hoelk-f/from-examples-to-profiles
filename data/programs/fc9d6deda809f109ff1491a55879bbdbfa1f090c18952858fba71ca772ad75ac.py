def transform(x: str) -> str:
    """
    Extracts the minute component from a datetime string formatted as
    'DD-Mon-YYYY HH:MM:SS' and returns it as a two‑digit string.
    """
    try:
        # Split off the time part after the space
        time_part = x.split()[-1]
        # Split the time into HH, MM, SS
        parts = time_part.split(":")
        # Return the minutes component
        return parts[1] if len(parts) > 1 else ""
    except Exception:
        return ""