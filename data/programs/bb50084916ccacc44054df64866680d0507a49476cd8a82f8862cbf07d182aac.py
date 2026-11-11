def transform(x: str) -> str:
    idx = x.find(":  ")
    if idx != -1:
        return x[idx + 3:]
    return x
