def transform(x: str) -> str:
    # Remove leading number and dot if present
    _, sep, rest = x.partition('.')
    if sep:
        rest = rest.lstrip()
    else:
        rest = x
    # Take the part before the first " - "
    first, _, _ = rest.partition(' - ')
    return first.strip()