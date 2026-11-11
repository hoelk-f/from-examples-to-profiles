def transform(x: str) -> str:
    """Extract the substring after the last semicolon, trimmed of surrounding whitespace."""
    parts = x.split(';')
    return parts[-1].strip()