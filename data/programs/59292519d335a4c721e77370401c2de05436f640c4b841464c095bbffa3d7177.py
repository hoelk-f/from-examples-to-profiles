def transform(x: str) -> str:
    """
    Extracts the substring between the first pair of curly braces.
    If the braces are not found, returns the original string unchanged.
    """
    start = x.find('{')
    end = x.find('}', start + 1)
    if start != -1 and end != -1:
        return x[start + 1:end]
    return x