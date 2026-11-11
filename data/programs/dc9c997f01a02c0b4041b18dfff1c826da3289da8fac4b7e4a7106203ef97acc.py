def transform(x: str) -> str:
    """
    Extracts the substring after the last semicolon in the input string,
    stripping any surrounding whitespace.
    """
    # Split the input on semicolons and take the last segment
    return x.split(';')[-1].strip()