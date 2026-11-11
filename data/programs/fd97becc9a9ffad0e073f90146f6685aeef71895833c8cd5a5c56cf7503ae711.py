def transform(x: str) -> str:
    """
    Extracts the seconds component from a datetime string formatted as
    'DD-MMM-YYYY HH:MM:SS'.
    """
    try:
        # Split date and time
        _, time_part = x.split()
        # Seconds are after the last colon
        return time_part.split(":")[-1]
    except Exception:
        # Fallback: return empty string if format is unexpected
        return ""