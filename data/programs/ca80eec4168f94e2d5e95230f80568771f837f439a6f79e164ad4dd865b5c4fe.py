def transform(x: str) -> str:
    idx = x.index("://") + 3
    idx = x.index("/", idx)
    return x[idx:]
