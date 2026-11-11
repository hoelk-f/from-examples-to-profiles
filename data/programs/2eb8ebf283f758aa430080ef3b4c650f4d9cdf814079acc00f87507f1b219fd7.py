def transform(x: str) -> str:
    _, _, rest = x.partition("=")
    return rest.strip()