def transform(x: str) -> str:
    """
    Remove any leading key and equals sign from the string and trim whitespace.
    Example: "model= super sonata" -> "super sonata"
    """
    if "=" in x:
        _, after = x.split("=", 1)
        return after.strip()
    return x.strip()