def transform(x: str) -> str:
    """
    Extracts the text inside the last pair of parentheses in the input string.
    """
    start = x.rfind('(')
    end = x.rfind(')')
    if start == -1 or end == -1 or end <= start:
        return ""
    return x[start + 1:end].strip()