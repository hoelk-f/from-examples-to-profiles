def transform(x: str) -> str:
    """
    Extracts the city name from a stadium description.
    The city is expected to appear after the first comma and before the next whitespace.
    """
    # Split on the first comma
    parts = x.split(",", 1)
    if len(parts) < 2:
        return ""
    # Take the part after the comma, strip leading/trailing whitespace
    after_comma = parts[1].strip()
    # The city is the first word before any whitespace
    city = after_comma.split()[0] if after_comma else ""
    return city