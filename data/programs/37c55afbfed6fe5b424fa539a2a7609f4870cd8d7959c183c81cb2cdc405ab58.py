def transform(x: str) -> str:
    idx = x.rfind(" @")
    if idx != -1:
        return x[:idx]
    return x
