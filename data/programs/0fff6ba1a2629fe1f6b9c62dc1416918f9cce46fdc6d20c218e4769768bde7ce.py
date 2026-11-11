def transform(x: str) -> str:
    """
    Extracts and returns the text inside the last pair of parentheses in the input string,
    stripped of surrounding whitespace. If no such parentheses exist, returns an empty string.
    """
    start = x.rfind('(')
    if start == -1:
        return ''
    end = x.find(')', start + 1)
    if end == -1:
        return ''
    return x[start + 1:end].strip()