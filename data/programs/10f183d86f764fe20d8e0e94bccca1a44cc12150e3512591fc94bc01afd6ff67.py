def transform(x: str) -> str:
    """
    Extracts the substring after the last semicolon in the input string,
    trimming any surrounding whitespace.
    """
    return x.split(";")[-1].strip()