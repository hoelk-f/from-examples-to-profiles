def transform(x: str) -> str:
    idx = x.index("://") + 3
    slash = x.index("/", idx)
    return x[slash:]
