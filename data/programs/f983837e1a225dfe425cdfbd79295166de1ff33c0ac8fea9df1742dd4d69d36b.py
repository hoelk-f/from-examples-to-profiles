def transform(x: str) -> str:
    """
    Remove everything up to and including the first '=' character,
    then strip surrounding whitespace.
    """
    if '=' in x:
        return x.split('=', 1)[1].strip()
    return x.strip()