def transform(x: str) -> str:
    """
    Extracts the numeric content inside the first pair of parentheses in the input string.
    If no such parentheses are found, returns an empty string.
    """
    start = x.find('(')
    end = x.find(')', start + 1)
    if start != -1 and end != -1:
        return x[start + 1:end]
    return ""