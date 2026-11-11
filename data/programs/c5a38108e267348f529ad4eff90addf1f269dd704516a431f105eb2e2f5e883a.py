def transform(x: str) -> str:
    idx = x.index('/', x.index('://') + 3)
    return x[idx:]
