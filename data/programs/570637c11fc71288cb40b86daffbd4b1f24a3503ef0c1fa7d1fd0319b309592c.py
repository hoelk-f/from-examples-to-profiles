def transform(x: str) -> str:
    rest = x.split("://", 1)[1]
    idx = rest.index("/")
    return rest[idx:]
