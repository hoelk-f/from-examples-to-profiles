def transform(x: str) -> str:
    idx = x.index(":")
    return x[idx + 1:].lstrip()
