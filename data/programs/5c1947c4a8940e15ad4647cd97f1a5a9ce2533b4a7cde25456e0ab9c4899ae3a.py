def transform(x: str) -> str:
    """
    Extracts the text following the substring 'Model:' in the input string,
    stripping any leading/trailing whitespace.
    If 'Model:' is not found, returns an empty string.
    """
    marker = "Model:"
    if marker in x:
        # Split on the first occurrence of the marker
        _, after = x.split(marker, 1)
        return after.strip()
    return ""