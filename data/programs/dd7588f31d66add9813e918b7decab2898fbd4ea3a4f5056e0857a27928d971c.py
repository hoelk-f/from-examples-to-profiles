def transform(x: str) -> str:
    """
    Remove the leading category label and any surrounding whitespace before the actual title.
    The category label is assumed to be the text before the first colon.
    """
    # Split on the first colon; if none, return the original string stripped of leading/trailing whitespace.
    parts = x.split(":", 1)
    if len(parts) == 2:
        return parts[1].lstrip()
    return x.strip()