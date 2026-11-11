def transform(x: str) -> str:
    _, sep, rest = x.partition(":")
    if not sep:
        return x.strip()
    return rest.lstrip()