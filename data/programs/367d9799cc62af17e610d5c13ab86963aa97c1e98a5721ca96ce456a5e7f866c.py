def transform(x: str) -> str:
    """
    Remove the outer <country>...</country> tags (or any similar XML-like tag)
    and return the inner text.
    """
    # Find the first closing angle bracket
    start = x.find('>')
    if start == -1:
        return x
    # Find the last opening angle bracket
    end = x.rfind('<')
    if end == -1 or end <= start:
        return x[start + 1 :]
    return x[start + 1 : end]