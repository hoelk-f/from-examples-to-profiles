def transform(x: str) -> str:
    """
    Extracts the content inside the last pair of parentheses in the string.
    """
    # Find the last opening parenthesis
    start = x.rfind('(')
    if start == -1:
        return ""
    # Find the closing parenthesis after the opening one
    end = x.find(')', start)
    if end == -1:
        return ""
    return x[start + 1:end]