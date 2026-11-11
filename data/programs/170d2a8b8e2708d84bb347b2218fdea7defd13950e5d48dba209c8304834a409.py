def transform(x: str) -> str:
    """
    Remove a leading key and equals sign from the string and strip surrounding whitespace.
    Example: "make= hyundai" -> "hyundai"
    """
    if "=" in x:
        _, rest = x.split("=", 1)
        return rest.strip()
    return x.strip()
