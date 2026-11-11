def transform(x: str) -> str:
    """
    Remove the leading key and equal sign from the string,
    then strip surrounding whitespace.
    """
    if '=' in x:
        _, rest = x.split('=', 1)
        return rest.strip()
    return x.strip()
