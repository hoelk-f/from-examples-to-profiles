def transform(x: str) -> str:
    """
    Removes the leading scheme and the '=//' delimiter from the input string,
    returning the remainder. If the delimiter is not present, returns the original string.
    """
    delimiter = "=//"
    if delimiter in x:
        return x.split(delimiter, 1)[1]
    return x