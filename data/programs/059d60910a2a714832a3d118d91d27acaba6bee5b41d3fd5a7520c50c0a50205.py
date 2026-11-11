def transform(x: str) -> str:
    # Remove leading numeric prefix ending with a dot and a space
    _, _, after_prefix = x.partition('. ')
    # Take the part before the first " -"
    first_part, _, _ = after_prefix.partition(' -')
    return first_part.strip()