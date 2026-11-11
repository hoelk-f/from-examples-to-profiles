def transform(x: str) -> str:
    """
    Remove a leading 'key=' pattern (including any whitespace after '=') from the string.
    If '=' is not present, return the stripped string.
    """
    if "=" in x:
        # Split at the first '=', take the part after it
        _, after = x.split("=", 1)
        return after.strip()
    return x.strip()