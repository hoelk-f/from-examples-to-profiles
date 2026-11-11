def transform(x: str) -> str:
    """
    Extracts the city name that appears after the first comma in the input string.
    The city is assumed to be the first whitespace-separated token after the comma.
    """
    # Find the position of the first comma
    idx = x.find(',')
    if idx == -1:
        # No comma found; return empty string
        return ''
    # Substring after the comma
    after_comma = x[idx + 1 :].strip()
    # The city is the first word before any whitespace
    city = after_comma.split()[0] if after_comma else ''
    return city