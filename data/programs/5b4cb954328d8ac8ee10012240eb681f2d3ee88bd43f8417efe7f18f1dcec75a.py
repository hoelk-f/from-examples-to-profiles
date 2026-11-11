def transform(x: str) -> str:
    rest = x[x.index("://") + 3:]
    slash = rest.index("/")
    return rest[slash:]
