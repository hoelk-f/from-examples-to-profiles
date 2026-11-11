def transform(x: str) -> str:
    """
    Extracts the uppercase country code found within parentheses in the input string.
    """
    start = x.rfind('(')
    end = x.rfind(')')
    if start != -1 and end != -1 and end > start:
        return x[start + 1:end].strip()
    return ""