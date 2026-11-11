def transform(x: str) -> str:
    sep = " - "
    idx = x.find(sep)
    return x[:idx] if idx != -1 else x