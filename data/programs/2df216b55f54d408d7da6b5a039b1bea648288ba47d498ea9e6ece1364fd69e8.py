def transform(x: str) -> str:
    """
    Extract the three‑letter country code that appears inside the last pair of
    parentheses in the given string.
    """
    # Find the last opening parenthesis
    start = x.rfind('(')
    if start == -1:
        return ""
    # Find the closing parenthesis after the opening one
    end = x.find(')', start)
    if end == -1:
        return ""
    # Return the trimmed content inside the parentheses
    return x[start + 1:end].strip()