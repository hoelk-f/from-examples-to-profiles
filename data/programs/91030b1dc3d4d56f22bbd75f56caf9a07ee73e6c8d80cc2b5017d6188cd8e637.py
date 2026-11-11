def transform(x: str) -> str:
    idx = x.index("://")
    path_start = x.index("/", idx + 3)
    return x[path_start:]
