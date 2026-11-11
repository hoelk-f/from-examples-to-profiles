def transform(x: str) -> str:
    """
    Extracts and returns the text inside the last pair of parentheses in the input string,
    without the surrounding parentheses. If no parentheses are found, returns an empty string.
    """
    start = x.rfind('(')
    end = x.rfind(')')
    if start != -1 and end != -1 and end > start:
        return x[start + 1:end].strip()
    return ""