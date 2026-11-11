def transform(x: str) -> str:
    """
    Extracts the seconds component from a datetime string of the form
    'dd-Mmm-yyyy HH:MM:SS' and returns it as a two‑digit string.
    """
    # Split the string into date and time parts
    parts = x.split()
    if len(parts) < 2:
        return ""
    time_part = parts[1]
    # Split the time into hour, minute, second
    t_components = time_part.split(":")
    if len(t_components) != 3:
        return ""
    # Return the seconds component
    return t_components[2]