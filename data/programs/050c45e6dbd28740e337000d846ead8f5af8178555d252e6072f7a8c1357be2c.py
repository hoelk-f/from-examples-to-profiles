def transform(x: str) -> str:
    """
    Extracts the minutes component from a datetime string formatted as
    "DD-MMM-YYYY HH:MM:SS" and returns it as a string.
    """
    try:
        # Split date and time
        _, time_part = x.strip().split()
        # Split time into hour, minute, second
        _, minute, _ = time_part.split(":")
        return minute
    except Exception:
        # Fallback: return empty string if format is unexpected
        return ""