def transform(x: str) -> str:
    """
    Extracts the substring after the first comma in the input string,
    stripping any leading or trailing whitespace.
    """
    parts = x.split(',', 1)
    return parts[1].strip() if len(parts) > 1 else x.strip()