def transform(x: str) -> str:
    """
    Removes the leading part up to and including the first '=' character,
    then strips any surrounding whitespace from the remainder.
    """
    if "=" in x:
        _, right = x.split("=", 1)
        return right.strip()
    return x.strip()