def transform(x: str) -> str:
    """
    Extracts the substring after the first comma in the input string,
    stripping any surrounding whitespace.
    """
    if ',' in x:
        return x.split(',', 1)[1].strip()
    return x.strip()