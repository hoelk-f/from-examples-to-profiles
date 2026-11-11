def transform(x: str) -> str:
    # Split off the part before the first " - "
    left, _, _ = x.partition(" - ")
    # Remove leading numeric prefix ending with a dot and a space
    _, _, rest = left.partition(". ")
    return rest if rest else left.strip()