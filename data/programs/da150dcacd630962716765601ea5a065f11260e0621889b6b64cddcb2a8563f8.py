def transform(x: str) -> str:
    """
    Extracts the content between the first closing '>' and the last opening '<'.
    If such delimiters are not found, returns the original string.
    """
    start = x.find('>')
    end = x.rfind('<')
    if start != -1 and end != -1 and start < end:
        return x[start + 1:end]
    return x.strip()