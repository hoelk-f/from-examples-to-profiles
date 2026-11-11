def transform(x: str) -> str:
    """
    Extract the latitude value from a string of the form
    "<latitude>(latitude), <longitude>(longitude)".
    """
    # Split at the marker "(latitude)" and take the part before it
    part = x.split("(latitude)")[0]
    # Remove any trailing commas or whitespace
    return part.rstrip(" ,\t\n\r")