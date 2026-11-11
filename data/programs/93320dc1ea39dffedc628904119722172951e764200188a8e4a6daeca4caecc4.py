def transform(x: str) -> str:
    # Remove leading numbering and dot
    _, _, rest = x.partition('. ')
    # Take the part before the hyphen separator
    first, _, _ = rest.partition(' - ')
    return first.strip()