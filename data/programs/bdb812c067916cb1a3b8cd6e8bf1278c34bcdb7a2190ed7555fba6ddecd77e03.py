def transform(x: str) -> str:
    """
    Extracts the uppercase country code enclosed in parentheses at the end of the string.
    If no such pattern is found, returns an empty string.
    """
    start = x.rfind('(')
    end = x.rfind(')')
    if start != -1 and end != -1 and start < end:
        return x[start + 1:end]
    return ""